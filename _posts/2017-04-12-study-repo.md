---
layout: post
title: Android源码解析之repo仓库
description: 用什么语言都可以封装git的命令，那为什么是python ？
author: 未知
date: 2017-04-04
share: true
comments: true
tag: Python
toc: true
---
<!-- MarkdownTOC -->

- [*1.Summary*{:.header2-font}](#1summaryheader2-font)
- [*2.About Repo*{:.header2-font}](#2about-repoheader2-font)
- [_3.Content_{:.header2-font}](#3contentheader2-font)
  - [_Repo仓库_{:.header3-font}](#repo仓库header3-font)
  - [_Manifest仓库_{:.header3-font}](#manifest仓库header3-font)
  - [*projects仓库集*{:.header3-font}](#projects仓库集header3-font)
- [*4.参考资料*{:.header2-font}](#4参考资料header2-font)

<!-- /MarkdownTOC -->

## *1.Summary*{:.header2-font}
&emsp;&emsp;首先说一下为什么会想分享这篇博客。出发点很简单，只是想学习一下Python在AOSP中的应用。repo应用就是一个研究的切入点。其次Python在深度学习、大数据都有一定的支持，后续会研究一下这方面的技术。最后就是个人喜好，无他。

## *2.About Repo*{:.header2-font}
&emsp;&emsp;repo就是通过Python封装git命令的应用。什么是[repo](https://source.android.com/source/developing.html)？简单来说就是对AOSP含有git仓库的各个项目的批处理。repo应用包括repo仓库（仓库也可以叫做项目）、manifest仓库、projectsc仓库集这三个核心。repo仓库都是一些Python文件，manifest仓库只有一个存放AOSP各个子项目元数据的xml文件。projects仓库集是AOSP各个子项目对应的git仓库。
*下面用一张图片表示一下。*

![architecture]({{site.baseurl}}/images/2017-04-12-repo_architecture.png)

补充一点，git是允许repository和working directory分布在不同的目录下的。所以就会看到AOSP的working directory在项目根目录而.git目录在.repo/projects目录

##  _3.Content_{:.header2-font}

&emsp;&emsp;先来草率的分析一下,拉取一套AOSP代码应该按照如下流程：

```bash
mkdir testsource  #创建AOSP目录。用于存放.repo应用和源码
cd testsource
repo init   -u  https://android.googlesource.com/platform/manifest -b android-4.0.1_r1
      cmd     #初始化repo仓库和manifest仓库                      
repo sync -j 8   
      cmd     #同步projects仓库集
repo start master --all 
      cmd     #创建并且切换到新分支上

repo仓库初始化--->manifest仓库初始化--->project仓库集初始化--->创建并切换到新分支上
```

&emsp;&emsp;从数据流自上而下看：

``repo command line --->optparse--->git command line``

&emsp;&emsp;在Python中使用的是optparse模块（后续将被argparse模块取代）解析命令行，所以optparse模块相当于数据转换中心将repo命名行转成git命令行

![repo init]({{site.baseurl}}/images/2017-04-12-repo_init_help.png)

### _Repo仓库_{:.header3-font}

&emsp;&emsp;接下来就看看具体的细节处理，从repo模块的入口函数main开始，执行的命令行如下：

``repo init   -u  https://android.googlesource.com/platform/manifest -b android-4.0.1_r1``

{%highlight python linenos%}
def main(orig_args):
  cmd, opt, args = _ParseArguments(orig_args)

  repo_main, rel_repo_dir = None, None
  # Don't use the local repo copy, make sure to switch to the gitc client first.
  if cmd != 'gitc-init':
    repo_main, rel_repo_dir = _FindRepo()

  wrapper_path = os.path.abspath(__file__)
  my_main, my_git = _RunSelf(wrapper_path)

  cwd = os.getcwd()
  ...
  if not repo_main:
    if opt.help:
      _Usage()
    if cmd == 'help':
      _Help(args)
    if not cmd:
      _NotInstalled()
    if cmd == 'init' or cmd == 'gitc-init':
      if my_git:
        _SetDefaultsTo(my_git)
      try:
        _Init(args, gitc_init=(cmd == 'gitc-init'))
      except CloneFailure:
        ...
        sys.exit(1)
      repo_main, rel_repo_dir = _FindRepo()
    else:
      _NoCommands(cmd)

  if my_main:
    repo_main = my_main

  ver_str = '.'.join(map(str, VERSION))
  me = [sys.executable, repo_main,
        '--repo-dir=%s' % rel_repo_dir,
        '--wrapper-version=%s' % ver_str,
        '--wrapper-path=%s' % wrapper_path,
        '--']
  me.extend(orig_args)
  me.extend(extra_args)
  try:
    os.execv(sys.executable, me)
  except OSError as e:
    ...
    sys.exit(148)
{%endhighlight%}

&emsp;&emsp;repo模块函数main(sys.argv[1:]) 参数sys.argv[1:]就是由command、options组成，然后由_ParseArguments函数解析。由于main函数流程复杂，我们考虑的是初次初始化。main函数在调用_Init函数之前对环境进行了检查：repo模块的版本号和路径、.repo/repo/路径下的main模块和git仓库。在_Init函数之后就是执行main模块中的入口函数_Main


_ParseArguments函数的代码如下：

```python
def _ParseArguments(args):
  cmd = None
  opt = _Options()
  arg = []
  for i in range(len(args)):
    a = args[i]
    if a == '-h' or a == '--help':
      opt.help = True

    elif not a.startswith('-'):
      cmd = a
      arg = args[i + 1:]
      break
  return cmd, opt, arg
```
&emsp;&emsp;_ParseArguments函数解析出cmd、opt、args，其中,cmd是init，args是command（init）后面的参数（-u https://android.googlesource.com/platform/manifest -b android-4.0.1_r1），而opt特指-h（--help）这样的用意在于当你输入repo -h,--help时就可以弹出一些帮助文档。

_FindRepo函数的代码如下：

```python
def _FindRepo():
  """Look for a repo installation, starting at the current directory.
  """
  curdir = os.getcwd()
  repo = None

  olddir = None
  while curdir != '/' \
          and curdir != olddir \
          and not repo:
    repo = os.path.join(curdir, repodir, REPO_MAIN)
    if not os.path.isfile(repo):
      repo = None
      olddir = curdir
      curdir = os.path.dirname(curdir)
  return (repo, os.path.join(curdir, repodir))
```
&emsp;&emsp;_FindRepo函数查找当前执行repo命令的目录下.repo/repo/main.py和.repo目录两者是否都存在。


_RunSelf函数的代码如下：

```python
def _RunSelf(wrapper_path):
  my_dir = os.path.dirname(wrapper_path)
  my_main = os.path.join(my_dir, 'main.py')
  my_git = os.path.join(my_dir, '.git')

  if os.path.isfile(my_main) and os.path.isdir(my_git):
    for name in ['git_config.py',
                 'project.py',
                 'subcmds']:
      if not os.path.exists(os.path.join(my_dir, name)):
        return None, None
    return my_main, my_git
  return None, None
```
&emsp;&emsp;_RunSelf函数检查repo模块的同级目录里是否有三个文件main.py 、git_config.py、project.py 和两个目录subcmds、.git。这次是查找运行中模块repo的同级目录，是否具备三个文件两个目录，如有具备这些，则.repo仓库之前就已经被初始化过了。反之，接下去就会初始化仓库。

&emsp;&emsp;接下来的各种控制流判断，取其中两个关键函数_SetDefaultsTo和_Init来详细讲解

```python
  ...
  if not repo_main:
    ...
    if cmd == 'init' or cmd == 'gitc-init':
      if my_git:
        _SetDefaultsTo(my_git)
      try:
        _Init(args, gitc_init=(cmd == 'gitc-init'))
      ...
```
&emsp;&emsp;repo_main,cmd,my_git这三个变量我们前面已经说过了它们的由来,其中的my_git如果存在，调用_SetDefaultsTo函数会设置数据源，反之，就是初次初始化，使用默认的数据源（REPO_URL = 'https://gerrit.googlesource.com/git-repo' ），那么就会克隆一个.repo/repo/仓库

_SetDefaultsTo函数

```python
def _SetDefaultsTo(gitdir):
  global REPO_URL
  global REPO_REV

  REPO_URL = gitdir
  proc = subprocess.Popen([GIT,
                           '--git-dir=%s' % gitdir,
                           'symbolic-ref',
                           'HEAD'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  REPO_REV = proc.stdout.read().strip()
  proc.stdout.close()

  proc.stderr.read()
  proc.stderr.close()

  if proc.wait() != 0:
    _print('fatal: %s has no current branch' % gitdir, file=sys.stderr)
    sys.exit(1)
```
&emsp;&emsp;--git-dir 指定git仓库的位置,symbolic-ref 指定当前分支为克隆分支这两者的值通过关键词global变成全局变量。

接下来就是核心函数_Init如下：

{%highlight python linenos%}
def _Init(args, gitc_init=False):
  """Installs repo by cloning it over the network.
  """
  ...
  opt, args = init_optparse.parse_args(args)
  if args:
    init_optparse.print_usage()
    sys.exit(1)

  url = opt.repo_url
  if not url:
    url = REPO_URL
    extra_args.append('--repo-url=%s' % url)

  branch = opt.repo_branch
  if not branch:
    branch = REPO_REV
    extra_args.append('--repo-branch=%s' % branch)

  if branch.startswith('refs/heads/'):
    branch = branch[len('refs/heads/'):]
  ...
  try:
    ...
    os.mkdir(repodir)
  except OSError as e:
    if e.errno != errno.EEXIST:
      ...
      sys.exit(1)

  _CheckGitVersion()
  try:
    if NeedSetupGnuPG():
      can_verify = SetupGnuPG(opt.quiet)
    else:
      can_verify = True

    dst = os.path.abspath(os.path.join(repodir, S_repo))
    _Clone(url, dst, opt.quiet, not opt.no_clone_bundle)

    if not os.path.isfile('%s/repo' % dst):
      _print("warning: '%s' does not look like a git-repo repository, is "
             "REPO_URL set correctly?" % url, file=sys.stderr)

    if can_verify and not opt.no_repo_verify:
      rev = _Verify(dst, branch, opt.quiet)
    else:
      rev = 'refs/remotes/origin/%s^0' % branch

    _Checkout(dst, branch, rev, opt.quiet)
  except CloneFailure:
    ...
{%endhighlight%}
&emsp;&emsp;_Init函数的参数    ``args=[-u,https://android.googlesource.com/platform/manifest,-b,android-4.0.1_r1]``     ,使用OptionParse类的成员函数parse_args解析得到opt对象（存储有url地址和分支号）和args列表（其值不为空时，便会停止创建仓库的进程）。既然得到了opt对象,那么接下来就要通过指定url地址和分支号去获取repo仓库、manifest仓库，由于命令行只有manifest仓库的地址，那么是不是就没有办法获取repo仓库了吗？google提供了自家repo仓库的url地址（``https://gerrit.googlesource.com/git-repo``）供开发者使用，也可以使用--repo-url选项指定自家公司repo仓库的url地址。接下来检查和配置环境

  - 1.需要支持1.7.2以上的git版本
  - 2.没有配置GnuPG的环境下，自动生成GnuPG文件

&emsp;&emsp;当GnuPG的环境配置好了，就会返回一个值can_verify，用于判断克隆完repo仓库后验证最新的tag是否被GunPG签过名，然后将克隆下来的repo仓库使用_Checkout函数切换到这个最新的tag，以便于使用最新的release版本（一般发布一个release版本都会打上一个tag），这就是这个tag的用意。

&emsp;&emsp;接下来我们就来看看函数_Init调用的两个核心函数_Clone和_Checkout

在这之前我们来看看git对远程仓库的操作图

![git operation flowchart]({{site.baseurl}}/images/2017-04-12-git_operation_flowchart.png)


_Clone函数的代码如下：

```python
def _Clone(url, local, quiet, clone_bundle):
  """Clones a git repository to a new subdirectory of repodir
  """
  try:
    os.mkdir(local)
  except OSError as e:
    ...
    raise CloneFailure()

  cmd = [GIT, 'init', '--quiet']
  try:
    proc = subprocess.Popen(cmd, cwd=local)
  except OSError as e:
    ...
    raise CloneFailure()
  if proc.wait() != 0:
    ...
    raise CloneFailure()

  _InitHttp()
  _SetConfig(local, 'remote.origin.url', url)
  _SetConfig(local,
             'remote.origin.fetch',
             '+refs/heads/*:refs/remotes/origin/*')
  if clone_bundle and _DownloadBundle(url, local, quiet):
    _ImportBundle(local)
  _Fetch(url, local, 'origin', quiet)
```
&emsp;&emsp;这里简单说一下_Clone函数的流程图。

``创建git仓库(git init)---> 初始化http网络  ----> 配置远程仓库url地址、分支名(git config)   ---> fetch记录从remote repository到local repository（git fetch）``


&emsp;&emsp;在有网络的条件下可以从远程仓库克隆代码，但是如果离线了怎么办？git给我们提供了一种bundle文件。
_DownloadBundle函数的代码如下:

{%highlight python linenos%}
def _DownloadBundle(url, local, quiet):
  if not url.endswith('/'):
    url += '/'
  url += 'clone.bundle'

  proc = subprocess.Popen(
      [GIT, 'config', '--get-regexp', 'url.*.insteadof'],
      cwd=local,
      stdout=subprocess.PIPE)
  for line in proc.stdout:
    m = re.compile(r'^url\.(.*)\.insteadof (.*)$').match(line)
    if m:
      new_url = m.group(1)
      old_url = m.group(2)
      if url.startswith(old_url):
        url = new_url + url[len(old_url):]
        break
  proc.stdout.close()
  proc.wait()

  if not url.startswith('http:') and not url.startswith('https:'):
    return False

  dest = open(os.path.join(local, '.git', 'clone.bundle'), 'w+b')
  try:
    try:
      r = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
      if e.code in [401, 403, 404, 501]:
        return False
      _print('fatal: Cannot get %s' % url, file=sys.stderr)
      _print('fatal: HTTP error %s' % e.code, file=sys.stderr)
      raise CloneFailure()
    except urllib.error.URLError as e:
      _print('fatal: Cannot get %s' % url, file=sys.stderr)
      _print('fatal: error %s' % e.reason, file=sys.stderr)
      raise CloneFailure()
    try:
      if not quiet:
        _print('Get %s' % url, file=sys.stderr)
      while True:
        buf = r.read(8192)
        if buf == '':
          return True
        dest.write(buf)
    finally:
      r.close()
  finally:
    dest.close()
{%endhighlight%}
&emsp;&emsp;在使用git fetch获取remote repository记录到local repository之前，其实代码的来源还可以从bundle获取。生成bundle之前需要在有网络的条件下，将远程仓库的记录存储在bundle中。
&emsp;&emsp;最后会调用_ImportBundle函数导入数据。这种导入方式的应用场景在于环境处于脱机状态，便可以从其他的机器拷贝一份bundle导入到自己的仓库中。_ImportBundle函数是对_Fetch函数进行包装,其中最为重要的就是第三个参数，指定了要导入到local repository的数据来源路径，可以是网络的url的仓库名，也可以是本地的bundle文件路径

_Checkout函数

{% highlight python linenos %}
def _Checkout(cwd, branch, rev, quiet):
  """Checkout an upstream branch into the repository and track it.
  """
  cmd = [GIT, 'update-ref', 'refs/heads/default', rev]
  if subprocess.Popen(cmd, cwd=cwd).wait() != 0:
    raise CloneFailure()

  _SetConfig(cwd, 'branch.default.remote', 'origin')
  _SetConfig(cwd, 'branch.default.merge', 'refs/heads/%s' % branch)

  cmd = [GIT, 'symbolic-ref', 'HEAD', 'refs/heads/default']
  if subprocess.Popen(cmd, cwd=cwd).wait() != 0:
    raise CloneFailure()

  cmd = [GIT, 'read-tree', '--reset', '-u']
  if not quiet:
    cmd.append('-v')
  cmd.append('HEAD')
  if subprocess.Popen(cmd, cwd=cwd).wait() != 0:
    raise CloneFailure()
{% endhighlight python %}

&emsp;&emsp;该函数对git chechout的底层函数进行封装，功能和git checkout切分支是一样的，至此我们的_Init函数就就执行完了，并且得到了repo仓库了那么接下来就是要得到manifest仓库了

```python
...
  ver_str = '.'.join(map(str, VERSION))
  me = [sys.executable, repo_main,
        '--repo-dir=%s' % rel_repo_dir,
        '--wrapper-version=%s' % ver_str,
        '--wrapper-path=%s' % wrapper_path,
        '--']
  me.extend(orig_args)
  me.extend(extra_args)
  try:
    os.execv(sys.executable, me)
...
```

### _Manifest仓库_{:.header3-font}
&emsp;&emsp;接下来就是执行main模块函数_Main，执行时命令行如下：

``/home/.../.repo/repo/main.py  --repo-dir=/home/.../.repo   --wrapper-version=1.0  --wrapper-path=/usr/bin/repo  -- init -u xxxx -b xxx``

&emsp;&emsp;其参数argv经过repo模块的扩展，添加了三个信息

- .repo目录的绝对路径
- repo模块内部定义的版本号
- repo模块的绝对路径

供直接或间接以Command为基类的衍生类的成员函数Execute调用.repo/repo/subcmds/*.py模块

_Main函数的代码如下：

{%highlight python linenos%}
def _Main(argv):
  result = 0

  opt = optparse.OptionParser(usage="repo wrapperinfo -- ...")
  opt.add_option("--repo-dir", dest="repodir",
                 help="path to .repo/")
  opt.add_option("--wrapper-version", dest="wrapper_version",
                 help="version of the wrapper script")
  opt.add_option("--wrapper-path", dest="wrapper_path",
                 help="location of the wrapper script")
  _PruneOptions(argv, opt)
  opt, argv = opt.parse_args(argv)

  _CheckWrapperVersion(opt.wrapper_version, opt.wrapper_path)
  _CheckRepoDir(opt.repodir)

  Version.wrapper_version = opt.wrapper_version
  Version.wrapper_path = opt.wrapper_path

  repo = _Repo(opt.repodir)
  try:
    try:
      init_ssh()
      init_http()
      result = repo._Run(argv) or 0
    finally:
      close_ssh()
  except KeyboardInterrupt:
    ...
    result = 1
  except ManifestParseError as mpe:
    ...
    result = 1
  except RepoChangedException as rce:
    # If repo changed, re-exec ourselves.
    #
    argv = list(sys.argv)
    argv.extend(rce.extra_args)
    try:
      os.execv(__file__, argv)
    except OSError as e:
      ...
      result = 128

  sys.exit(result)
if __name__ == '__main__':
  _Main(sys.argv[1:])
{%endhighlight%}

&emsp;&emsp;_Main函数的重点部分在于repo调用_Repo类中的_Run函数，而前期也如repo和main两个模块一样做一些必要的检查。修剪命令的_PruneOptions函数、解析命令的parse_args函数(opt"--"之前的内容，argv"--"之后的内容)、检查repo脚本版本的_CheckWrapperVersion函数、检查.repo目录是否存在的_CheckRepoDir函数。

_Repo类的代码如下：

{%highlight python linenos%}
from subcmds import all_commands

class _Repo(object):
  def __init__(self, repodir):
    self.repodir = repodir
    self.commands = all_commands
    # add 'branch' as an alias for 'branches'
    all_commands['branch'] = all_commands['branches']

  def _Run(self, argv):
    result = 0
    name = None
    glob = []

    for i in range(len(argv)):
      if not argv[i].startswith('-'):
        name = argv[i]
        if i > 0:
          glob = argv[:i]
        argv = argv[i + 1:]
        break
    if not name:
      glob = argv
      name = 'help'
      argv = []
    gopts, _gargs = global_options.parse_args(glob)
    ...
    try:
      cmd = self.commands[name]
    except KeyError:
      ...
      return 1

    cmd.repodir = self.repodir
    cmd.manifest = XmlManifest(cmd.repodir)
    ...

    Editor.globalConfig = cmd.manifest.globalConfig
    ...
    try:
      copts, cargs = cmd.OptionParser.parse_args(argv)
      copts = cmd.ReadEnvironmentOptions(copts)
    except NoManifestException as e:
      ...
      return 1
    ...

    start = time.time()
    try:
      result = cmd.Execute(copts, cargs)
    except (DownloadError, ManifestInvalidRevisionError,
        NoManifestException) as e:
      ...
      result = 1
    except NoSuchProjectError as e:
      ...
      result = 1
    except InvalidProjectGroupsError as e:
      ...
      result = 1
    finally:
      elapsed = time.time() - start
      hours, remainder = divmod(elapsed, 3600)
      minutes, seconds = divmod(remainder, 60)
      if gopts.time:
        if hours == 0:
          print('real\t%dm%.3fs' % (minutes, seconds), file=sys.stderr)
        else:
          print('real\t%dh%dm%.3fs' % (hours, minutes, seconds),
                file=sys.stderr)

    return result
{%endhighlight%}
&emsp;&emsp;_Repo类的有两个成员变量：repodir、commands和一个类变量all_commands，其中的all_commands的值是一些命令的类名，通过包subcmds初始化代码，将包subcmds下的模块名首字母转化为大写其余字母不变，就是命令的类名。在结合Run函数，可以知道，该类主要用于分发被解析后的cmd在包subcmds下所对应的模块里面的类（比如：init指令--->from init import Init）。
&emsp;&emsp;_Repo类的成员函数_Run主要是初始化XmlManifest，和调用Command类的成员函数Execute。

其中XmlManifest类用于管理.repo，XmlManifest类的代码如下：

```python
class XmlManifest(object):
  """manages the repo configuration file"""

  def __init__(self, repodir):
    self.repodir = os.path.abspath(repodir)
    self.topdir = os.path.dirname(self.repodir)
    self.manifestFile = os.path.join(self.repodir, MANIFEST_FILE_NAME)
    self.globalConfig = GitConfig.ForUser()
    self.localManifestWarning = False
    self.isGitcClient = False

    self.repoProject = MetaProject(self, 'repo',
      gitdir   = os.path.join(repodir, 'repo/.git'),
      worktree = os.path.join(repodir, 'repo'))

    self.manifestProject = MetaProject(self, 'manifests',
      gitdir   = os.path.join(repodir, 'manifests.git'),
      worktree = os.path.join(repodir, 'manifests'))
```

XmlManifest类在manifest_xml模块里面，XmlManifest类的主要成员变量有：

  + repodir:.repo目录的绝对路径
  + topdir：AOSP项目的绝对路径（testsource目录绝对路径）
  + manifestFile：.repo目录下的链接文件manifest.xml
  + repoProject： .repo目录下的repo仓库
  + manifestProject：.repo目录下的manifest仓库

类中还提供了对.repo的属性值和及其操作的成员函数。所以不难看出该类就是对.repo目录的管理工具。我们在继续看一下该类中重要的成员变量repoProject、manifestProject，都是MetaProject类的对象.

MetaProject类的代码如下

```python
class MetaProject(Project):
  """A special project housed under .repo.
  """
  def __init__(self, manifest, name, gitdir, worktree):
    Project.__init__(self,
                     manifest=manifest,
                     name=name,
                     gitdir=gitdir,
                     objdir=gitdir,
                     worktree=worktree,
                     remote=RemoteSpec('origin'),
                     relpath='.repo/%s' % name,
                     revisionExpr='refs/heads/master',
                     revisionId=None,
                     groups=None)

```
成员变量如下：

- manifest:是XmlManifest类的对象
- name:创建新仓库的名字
- gitdir: .git仓库的绝对路径
- worktree:工作目录
- remote：远程仓库
- relpath：创建新仓库的相对于.repo目录的路径
- revisionExpr： 分支
MetaProject和Projects是一样的，不过为了体现这两个仓库（repo仓库和manifest仓库）在AOSP项目整个仓库集的重要性，才会有这样的命名。


Project类的代码如下：

{%highlight python linenos%}
class Project(object):
  # These objects can be shared between several working trees.
  shareable_files = ['description', 'info']
  shareable_dirs = ['hooks', 'objects', 'rr-cache', 'svn']
  # These objects can only be used by a single working tree.
  working_tree_files = ['config', 'packed-refs', 'shallow']
  working_tree_dirs = ['logs', 'refs']
  def __init__(self,
               manifest,
               name,
               remote,
               gitdir,
               objdir,
               worktree,
               relpath,
               revisionExpr,
               revisionId,
               rebase=True,
               groups=None,
               sync_c=False,
               sync_s=False,
               clone_depth=None,
               upstream=None,
               parent=None,
               is_derived=False,
               dest_branch=None,
               optimized_fetch=False,
               old_revision=None):
    """Init a Project object.

    Args:
      manifest: The XmlManifest object.
      name: The `name` attribute of manifest.xml's project element.
      remote: RemoteSpec object specifying its remote's properties.
      gitdir: Absolute path of git directory.
      objdir: Absolute path of directory to store git objects.
      worktree: Absolute path of git working tree.
      relpath: Relative path of git working tree to repo's top directory.
      revisionExpr: The `revision` attribute of manifest.xml's project element.
      revisionId: git commit id for checking out.
      rebase: The `rebase` attribute of manifest.xml's project element.
      groups: The `groups` attribute of manifest.xml's project element.
      sync_c: The `sync-c` attribute of manifest.xml's project element.
      sync_s: The `sync-s` attribute of manifest.xml's project element.
      upstream: The `upstream` attribute of manifest.xml's project element.
      parent: The parent Project object.
      is_derived: False if the project was explicitly defined in the manifest;
                  True if the project is a discovered submodule.
      dest_branch: The branch to which to push changes for review by default.
      optimized_fetch: If True, when a project is set to a sha1 revision, only
                       fetch from the remote if the sha1 is not present locally.
      old_revision: saved git commit id for open GITC projects.
    """
    self.manifest = manifest
    self.name = name
    self.remote = remote
    self.gitdir = gitdir.replace('\\', '/')
    self.objdir = objdir.replace('\\', '/')
    if worktree:
      self.worktree = worktree.replace('\\', '/')
    else:
      self.worktree = None
    self.relpath = relpath
    self.revisionExpr = revisionExpr

    if   revisionId is None \
     and revisionExpr \
     and IsId(revisionExpr):
      self.revisionId = revisionExpr
    else:
      self.revisionId = revisionId

    self.rebase = rebase
    self.groups = groups
    self.sync_c = sync_c
    self.sync_s = sync_s
    self.clone_depth = clone_depth
    self.upstream = upstream
    self.parent = parent
    self.is_derived = is_derived
    self.optimized_fetch = optimized_fetch
    self.subprojects = []

    self.snapshots = {}
    self.copyfiles = []
    self.linkfiles = []
    self.annotations = []
    self.config = GitConfig.ForRepository(
                    gitdir=self.gitdir,
                    defaults=self.manifest.globalConfig)

    if self.worktree:
      self.work_git = self._GitGetByExec(self, bare=False, gitdir=gitdir)
    else:
      self.work_git = None
    self.bare_git = self._GitGetByExec(self, bare=True, gitdir=gitdir)
    self.bare_ref = GitRefs(gitdir)
    self.bare_objdir = self._GitGetByExec(self, bare=True, gitdir=objdir)
    self.dest_branch = dest_branch
    self.old_revision = old_revision

    # This will be filled in if a project is later identified to be the
    # project containing repo hooks.
    self.enabled_repo_hooks = []
{%endhighlight%}
&emsp;&emsp;Project是用来描述AOSP项目某一个仓库（或者说项目）,其中有几个重要的值是来源于manifest.xml,   ``name,revisionExpr,rebase,groups,sync_c,sync_s,upstream``      这几个值对应到manifest.xml中某个标签的属性值。所以AOSP项目的仓库信息都在manifest.xml,除了repo仓库和manifest仓库

&emsp;&emsp;现在我们回到成员函数_Run的流程中，XmlManifest类已经构造完了，接下来就是调用Execute。

&emsp;&emsp;Command类是所有指令（init、sync、start）的基类，其成员函数Execute被指令override，故调用成员函数Execute就可以执行某个指令对应的成员函数Execute。所以，执行到这一行(result = cmd.Execute(copts, cargs))的时候,就是整个架构的分水岭了。下面的图片是对前面的总结。

![repo _Repo#_Run flowchart]({{site.baseurl | prepend:site.url}}/images/2017-04-12-repo__Repo_Run_flowchart.png){:.white-bg-image}


接下来就是执行init模块中Init类的成员函数Execute：

```python
class Init(InteractiveCommand, MirrorSafeCommand):
  ...

  def Execute(self, opt, args):
    git_require(MIN_GIT_VERSION, fail=True)

    if opt.reference:
      opt.reference = os.path.expanduser(opt.reference)

    # Check this here, else manifest will be tagged "not new" and init won't be
    # possible anymore without removing the .repo/manifests directory.
    if opt.archive and opt.mirror:
      ...
      sys.exit(1)

    self._SyncManifest(opt)
    self._LinkManifest(opt.manifest_name)

    if os.isatty(0) and os.isatty(1) and not self.manifest.IsMirror:
      if opt.config_name or self._ShouldConfigureUser():
        self._ConfigureUser()
      self._ConfigureColor()

    self._ConfigureDepth(opt)

    self._DisplayResult()
```
&emsp;&emsp;Init类的成员函数Execute的重点在于两个成员函数_SyncManifest和_LinkManifest，前者会克隆出manifest仓库，后者会通过os模块symlink函数生成链接文件manifest.xml。

_SyncManifest函数的代码如下：

{%highlight python linenos%}
class Init(InteractiveCommand, MirrorSafeCommand):
  ...

  def _SyncManifest(self, opt):
    m = self.manifest.manifestProject
    is_new = not m.Exists

    if is_new:
      ...

      m._InitGitDir(mirror_git=mirrored_manifest_git)

      if opt.manifest_branch:
        m.revisionExpr = opt.manifest_branch
      else:
        m.revisionExpr = 'refs/heads/master'
    else:
      if opt.manifest_branch:
        m.revisionExpr = opt.manifest_branch
      else:
        m.PreSync()

    ...

    if not m.Sync_NetworkHalf(is_new=is_new, quiet=opt.quiet,
        clone_bundle=not opt.no_clone_bundle,
        current_branch_only=opt.current_branch_only,
        no_tags=opt.no_tags):
      r = m.GetRemote(m.remote.name)
      print('fatal: cannot obtain manifest %s' % r.url, file=sys.stderr)

      # Better delete the manifest git dir if we created it; otherwise next
      # time (when user fixes problems) we won't go through the "is_new" logic.
      if is_new:
        shutil.rmtree(m.gitdir)
      sys.exit(1)

    if opt.manifest_branch:
      m.MetaBranchSwitch()

    syncbuf = SyncBuffer(m.config)
    m.Sync_LocalHalf(syncbuf)
    syncbuf.Finish()

    if is_new or m.CurrentBranch is None:
      if not m.StartBranch('default'):
        print('fatal: cannot create default in manifest', file=sys.stderr)
        sys.exit(1)
{%endhighlight%}
&emsp;&emsp;Init类的成员函数_SyncManifest会克隆一个仓库，流程一般如下：git init--->git fetch--->git checkout branch_name。对应的Project类成员函数就是_InitGitDir，Sync_NetworkHalf，Sync_LocalHalf,是不是很熟悉，跟克隆repo仓库的流程是一样的，其实repo仓库、manifest仓库、projects仓库集这些仓库克隆出来的方式是一样的。


```python
class Project(object): 
  ...

  def _InitGitDir(self, mirror_git=None, force_sync=False):
    init_git_dir = not os.path.exists(self.gitdir)
    init_obj_dir = not os.path.exists(self.objdir)
    try:
      # Initialize the bare repository, which contains all of the objects.
      if init_obj_dir:
        os.makedirs(self.objdir)
        self.bare_objdir.init()
     ...
```

&emsp;&emsp;其中类_GitGetByExec的对象封装了操作仓库的命令。比如git init。但是却找不到成员函数init，原来成员函数init时动态定义的。关键的地方就在于_GitGetByExec类的成员函数_getattr_。

_GitGetByExec类的成员函数__getattr__代码如下:

{%highlight python linenos%}
class Project(object): 
  ...

  class _GitGetByExec(object): 
  ...

    def __getattr__(self, name):
      ...
      name = name.replace('_', '-')

      def runner(*args, **kwargs):
        cmdv = []
        config = kwargs.pop('config', None)
        ...
        if config is not None:
          if not git_require((1, 7, 2)):
            raise ValueError('cannot set config on command line for %s()'
                             % name)
          for k, v in config.items():
            cmdv.append('-c')
            cmdv.append('%s=%s' % (k, v))
        cmdv.append(name)
        cmdv.extend(args)
        p = GitCommand(self._project,
                       cmdv,
                       bare=self._bare,
                       gitdir=self._gitdir,
                       capture_stdout=True,
                       capture_stderr=True)
        if p.Wait() != 0:
          raise GitError('%s %s: %s' %
                         (self._project.name, name, p.stderr))
        r = p.stdout
        try:
          r = r.decode('utf-8')
        except AttributeError:
          pass
        if r.endswith('\n') and r.index('\n') == len(r) - 1:
          return r[:-1]
        return r
      return runner
{%endhighlight%}
&emsp;&emsp;_GitGetByExec类通过成员函数__getattr__可以向工厂一样生产一些执行git命令的成员函数。既然仓库已经初始化好了，那么接下来就是fetch仓库了。

Sync_NetworkHalf成员函数的代码如下：

```python
class Project(object):  
  ... 

  def Sync_NetworkHalf(self,
                       quiet=False,
                       is_new=None,
                       current_branch_only=False,
                       force_sync=False,
                       clone_bundle=True,
                       no_tags=False,
                       archive=False,
                       optimized_fetch=False,
                       prune=False):
    ...
    if (need_to_fetch and
        not self._RemoteFetch(initial=is_new, quiet=quiet, alt_dir=alt_dir,
                              current_branch_only=current_branch_only,
                              no_tags=no_tags, prune=prune, depth=depth)):
      return False

    if self.worktree:
      self._InitMRef()
    else:
      self._InitMirrorHead()
      try:
        os.remove(os.path.join(self.gitdir, 'FETCH_HEAD'))
      except OSError:
        pass
    return True
```

&emsp;&emsp;Project类Sync_NetworkHalf方法调用_RemoteFetch方法实现了从远程仓库fetch记录到本地仓库，_RemoteFetch函数其实是"git fetch"命令的封装。

Sync_LocalHalf成员函数的代码如下：

{%highlight python linenos%}
class Project(object):  
  ...

  def Sync_LocalHalf(self, syncbuf, force_sync=False):
    """Perform only the local IO portion of the sync process.
       Network access is not required.
    """
    ...
    revid = self.GetRevisionId(all_refs)

    def _doff():
      self._FastForward(revid)
      self._CopyAndLinkFiles()

    head = self.work_git.GetHead()
    ...

    if branch is None or syncbuf.detach_head:
      # Currently on a detached HEAD.  The user is assumed to
      # not have any local modifications worth worrying about.
      #
      ...

      if head == revid:
        # No changes; don't do anything further.
        # Except if the head needs to be detached
        #
        if not syncbuf.detach_head:
          # The copy/linkfile config may have changed.
          self._CopyAndLinkFiles()
          return
      else:
        lost = self._revlist(not_rev(revid), HEAD)
        if lost:
          syncbuf.info(self, "discarding %d commits", len(lost))

      try:
        self._Checkout(revid, quiet=True)
      except GitError as e:
        syncbuf.fail(self, e)
        return
      self._CopyAndLinkFiles()
      return

    if head == revid:
      # No changes; don't do anything further.
      #
      # The copy/linkfile config may have changed.
      self._CopyAndLinkFiles()
      return

    branch = self.GetBranch(branch)

    if not branch.LocalMerge:
      # The current branch has no tracking configuration.
      # Jump off it to a detached HEAD.
      #
      ...
      try:
        self._Checkout(revid, quiet=True)
      except GitError as e:
        syncbuf.fail(self, e)
        return
      self._CopyAndLinkFiles()
      return

    upstream_gain = self._revlist(not_rev(HEAD), revid)
    pub = self.WasPublished(branch.name, all_refs)
    if pub:
      not_merged = self._revlist(not_rev(revid), pub)
      if not_merged:
        ...
        return
      elif pub == head:
        # All published commits are merged, and thus we are a
        # strict subset.  We can fast-forward safely.
        #
        syncbuf.later1(self, _doff)
        return

    # Examine the local commits not in the remote.  Find the
    # last one attributed to this user, if any.
    #
    local_changes = self._revlist(not_rev(revid), HEAD, format='%H %ce')
    last_mine = None
    cnt_mine = 0
    for commit in local_changes:
      commit_id, committer_email = commit.decode('utf-8').split(' ', 1)
      if committer_email == self.UserEmail:
        last_mine = commit_id
        cnt_mine += 1

    if not upstream_gain and cnt_mine == len(local_changes):
      return

    ...

    branch.remote = self.GetRemote(self.remote.name)
    if not ID_RE.match(self.revisionExpr):
      # in case of manifest sync the revisionExpr might be a SHA1
      branch.merge = self.revisionExpr
      if not branch.merge.startswith('refs/'):
        branch.merge = R_HEADS + branch.merge
    branch.Save()

    if cnt_mine > 0 and self.rebase:
      def _dorebase():
        self._Rebase(upstream='%s^1' % last_mine, onto=revid)
        self._CopyAndLinkFiles()
      syncbuf.later2(self, _dorebase)
    elif local_changes:
      try:
        self._ResetHard(revid)
        self._CopyAndLinkFiles()
      except GitError as e:
        syncbuf.fail(self, e)
        return
    else:
      syncbuf.later1(self, _doff)
{%endhighlight%}

&emsp;&emsp;Project类的成员函数Sync_LocalHalf内部流程较为复杂，这里我们只讲checkout到一个干净的分支。

_LinkManifest成员函数的代码如下：

```python
class Init(InteractiveCommand, MirrorSafeCommand):  
  ...

  def _LinkManifest(self, name):
    if not name:
      print('fatal: manifest name (-m) is required.', file=sys.stderr)
      sys.exit(1)

    try:
      self.manifest.Link(name)
    except ManifestParseError as e:
      print("fatal: manifest '%s' not available" % name, file=sys.stderr)
      print('fatal: %s' % str(e), file=sys.stderr)
      sys.exit(1)
```
&emsp;&emsp;成员函数_LinkManifest最终会调用os.symlink，创建manifest目录下default.xml的链接文件manifest.xml，这样方便访问manifest.xml文件

### *projects仓库集*{:.header3-font}









## *4.参考资料*{:.header2-font}
[Android Open Source Project](https://source.android.com/source/developing)
[Android源代码仓库及其管理工具Repo分析](http://blog.csdn.net/luoshengyang/article/details/18195205)

