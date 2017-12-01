---
layout: post
title: AOSP(SYS) --- repo工具
description: 用什么语言都可以封装git的命令，那为什么是python ?
date: 2017-04-12
share: true
comments: true
tag: 
- Python
- Tools
- AOSP(SYS)
---
<!-- MarkdownTOC -->

- [*1.Summary*{:.header2-font}](#1summaryheader2-font)
- [*2.About Repo*{:.header2-font}](#2about-repoheader2-font)
- [_3.Introduction_{:.header2-font}](#3introductionheader2-font)
  - [_Repo仓库_{:.header3-font}](#repo仓库header3-font)
  - [_Manifest仓库_{:.header3-font}](#manifest仓库header3-font)
  - [*Projects仓库集*{:.header3-font}](#projects仓库集header3-font)
  - [*创建分支*{:.header3-font}](#创建分支header3-font)
- [*4.Reference*{:.header2-font}](#4referenceheader2-font)

<!-- /MarkdownTOC -->

## *1.Summary*{:.header2-font}
&emsp;&emsp;首先说一下为什么会想分享这篇博客。出发点很简单，只是想学习一下Python在AOSP中的应用。repo应用就是一个研究的切入点。其次Python在深度学习、大数据都有一定的支持，后续会研究一下这方面的技术。最后就是个人喜好，无他。

## *2.About Repo*{:.header2-font}
&emsp;&emsp;repo就是通过Python封装git命令的应用。什么是[repo](https://source.android.com/source/developing.html)？简单来说就是对AOSP含有git仓库的各个项目的批处理。repo应用包括repo仓库（仓库也可以叫做项目）、manifest仓库、projectsc仓库集这三个核心。repo仓库都是一些Python文件，manifest仓库只有一个存放AOSP各个子项目元数据的xml文件。projects仓库集是AOSP各个子项目对应的git仓库。
*下面用一张图片表示一下。*

![architecture]({{site.baseurl}}/asset/2017-04-12/2017-04-12-repo_architecture.png)

补充一点，git是允许repository和working directory分布在不同的目录下的。所以就会看到AOSP的working directory在项目根目录而.git目录在.repo/projects目录

##  _3.Introduction_{:.header2-font}

&emsp;&emsp;先来草率的分析一下,拉取一套AOSP代码应该按照如下流程：

{%highlight bash linenos%}
mkdir testsource  #创建AOSP目录。用于存放.repo应用和源码
cd testsource
repo init   -u  https://android.googlesource.com/platform/manifest -b android-4.0.1_r1
      cmd     #初始化repo仓库和manifest仓库                      
repo sync -j 8   
      cmd     #同步projects仓库集
repo start master --all 
      cmd     #创建并且切换到新分支上

repo仓库初始化--->manifest仓库初始化--->project仓库集初始化--->创建并切换到新分支上
{%endhighlight%}

&emsp;&emsp;从数据流自上而下看：

``repo command line --->optparse--->git command line``

&emsp;&emsp;在Python中使用的是optparse模块（后续将被argparse模块取代）解析命令行，所以optparse模块相当于数据转换中心将repo命名行转成git命令行

![repo init]({{site.baseurl}}/asset/2017-04-12/2017-04-12-repo_init_help.png)

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

{%highlight python%}
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
{%endhighlight%}
&emsp;&emsp;_ParseArguments函数解析出cmd、opt、args，其中,cmd是init，args是command（init）后面的参数（-u https://android.googlesource.com/platform/manifest -b android-4.0.1_r1），而opt特指-h（--help）这样的用意在于当你输入repo -h,--help时就可以弹出一些帮助文档。

_FindRepo函数的代码如下：

{%highlight python%}
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
{%endhighlight%}
&emsp;&emsp;_FindRepo函数查找当前执行repo命令的目录下.repo/repo/main.py和.repo目录两者是否都存在。


_RunSelf函数的代码如下：

{%highlight python%}
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
{%endhighlight%}
&emsp;&emsp;_RunSelf函数检查repo模块的同级目录里是否有三个文件main.py 、git_config.py、project.py 和两个目录subcmds、.git。这次是查找运行中模块repo的同级目录，是否具备三个文件两个目录，如有具备这些，则.repo仓库之前就已经被初始化过了。反之，接下去就会初始化仓库。

&emsp;&emsp;接下来的各种控制流判断，取其中两个关键函数_SetDefaultsTo和_Init来详细讲解

{%highlight python%}
  ...
  if not repo_main:
    ...
    if cmd == 'init' or cmd == 'gitc-init':
      if my_git:
        _SetDefaultsTo(my_git)
      try:
        _Init(args, gitc_init=(cmd == 'gitc-init'))
      ...
{%endhighlight%}
&emsp;&emsp;repo_main,cmd,my_git这三个变量我们前面已经说过了它们的由来,其中的my_git如果存在，调用_SetDefaultsTo函数会设置数据源，反之，就是初次初始化，使用默认的数据源（REPO_URL = 'https://gerrit.googlesource.com/git-repo' ），那么就会克隆一个.repo/repo/仓库

_SetDefaultsTo函数

{%highlight python%}
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
{%endhighlight%}
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

![git operation flowchart]({{site.baseurl}}/asset/2017-04-12/2017-04-12-git_operation_flowchart.png)


_Clone函数的代码如下：

{%highlight python linenos%}
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
{%endhighlight%}
&emsp;&emsp;这里简单说一下_Clone函数的流程图。

``创建git仓库(git init)---> 初始化http网络  ----> 配置远程仓库url地址、分支名(git config)   ---> fetch记录从remote repository到local repository（git fetch）``


&emsp;&emsp;在有网络的条件下可以从远程仓库克隆代码，但是如果离线了怎么办？git给我们提供了一种bundle机制。
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
      ...
      raise CloneFailure()
    except urllib.error.URLError as e:
      ...
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
&emsp;&emsp;最后会调用_ImportBundle函数导入数据。这种导入方式的应用场景在于环境处于脱机状态，便可以从其他的机器拷贝一份bundle导入到自己的仓库中。_ImportBundle函数是对_Fetch函数进行包装,其中最为重要的就是第三个参数，指定了要导入到local repository的数据来源路径，可以是网络的 url 的仓库名，也可以是本地的bundle路径

_Checkout函数

{%highlight python linenos%}
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
{%endhighlight%}

&emsp;&emsp;该函数对git chechout的底层函数进行封装，功能和git checkout切分支是一样的，至此我们的_Init函数就执行完了，并且得到了repo仓库了那么接下来就是要得到manifest仓库了

{%highlight python linenos%}
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
{%endhighlight%}

### _Manifest仓库_{:.header3-font}
&emsp;&emsp;接下来就是执行main模块函数_Main，执行时命令行如下：

``/home/.../.repo/repo/main.py  --repo-dir=/home/.../.repo   --wrapper-version=1.0  --wrapper-path=/usr/bin/repo  -- init -u xxxx -b xxx``

&emsp;&emsp;其参数argv经过repo模块的扩展，添加了三个信息

- .repo目录的绝对路径
- repo模块内部定义的版本号
- repo模块的绝对路径

经过repo模块添加的信息用来检查是否有可用的repo和执行main模块，这是命令行的前部分，而后半部分（init -u xxxx -b xxx）供直接或间接以Command为基类的衍生类的成员函数Execute调用放置在.repo/repo/subcmds/目录下的*.py模块。repo脚本能执行的命令都是放在该目录下的，一个Python文件对应一个repo命令。比如："repo init"表示要执行的模块在.repo/repo/subcmds/init.py。

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

&emsp;&emsp;_Main函数的重点部分在于repo调用_Repo类中的成员函数_Run，而前期也如repo和main两个模块一样做一些必要的检查。修剪命令行的_PruneOptions函数、解析命令的parse_args函数(opt为"--"之前的内容，argv"为--"之后的内容)、检查repo模块版本的_CheckWrapperVersion函数、检查 .repo目录是否存在的_CheckRepoDir函数。

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
&emsp;&emsp;_Repo类有两个成员变量repodir、commands和一个类变量all_commands，其中all_commands字典的值是一些repo脚本能够执行命令的类名。那这些值是怎么来的呢 ？ 在 ``from subcmds import all_commands`` 时，就会初始化subcmds包，将subcmds目录下所有模块名的首字母转化为大写其余字母不变，就成了命令的类名。再结合成员函数_Run，可以知道，该类的作用在于，将解析后的cmd分发到包subcmds下所对应的模块里面的类（比如：init指令--->subcmds/init.py里面的Init类）。
&emsp;&emsp;_Repo类的成员函数_Run主要是初始化XmlManifest，获取某个指令独有OptionParse并解析指令，调用Command类的成员函数Execute。

其中XmlManifest类用于管理 .repo，XmlManifest类的代码如下：

{%highlight python linenos%}
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
{%endhighlight%}
XmlManifest类在manifest_xml模块里面，XmlManifest类的主要成员变量有：

  + repodir:.repo目录的绝对路径
  + topdir：AOSP项目的绝对路径（testsource目录绝对路径）
  + manifestFile：.repo目录下的链接文件manifest.xml
  + repoProject： .repo目录下的repo仓库
  + manifestProject：.repo目录下的manifest仓库

类中还提供了对.repo的属性值和对属性值操作的成员函数，比如加载数据到XmlManifest对象(_Load成员函数)和重置数据(_Unload成员函数)，创建manifest.xml链接文件（Link成员函数），获取projects目录下的仓库对象（GetProjectsWithName，GetProjectPaths成员函数）。所以不难看出该类就是对.repo目录的管理工具。我们在继续看一下该类中重要的成员变量repoProject、manifestProject，都是MetaProject类的对象.

MetaProject类的代码如下

{%highlight python linenos%}
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
{%endhighlight%}
成员变量如下：

- manifest:是XmlManifest类的对象
- name:创建新仓库的名字
- gitdir: .git仓库的绝对路径
- worktree:工作目录
- remote：远程仓库
- relpath：创建新仓库的相对于.repo目录的路径
- revisionExpr： 分支
 
MetaProject和Project对于仓库的操作逻辑差不多一样，不过为了体现这两个仓库（repo仓库和manifest仓库）在AOSP项目整个仓库集的重要性，才会有这样的命名。


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

&emsp;&emsp;Project是用来描述AOSP项目某一个仓库（或者说项目）,其中有几个重要的值是来源于manifest.xml,   ``name,revisionExpr,rebase,groups,sync_c,sync_s,upstream``      这几个值对应到manifest.xml中某个标签的属性值，后续我们在克隆projects仓库集会讲解manifest标签和属性的用途。所以AOSP项目的仓库信息都在manifest.xml,除了repo仓库和manifest仓库，这些信息是在我们使用"repo sync"时会用到。

&emsp;&emsp;现在我们回到成员函数_Run的流程中，XmlManifest类已经构造完了。``cmd.OptionParser.parse_args(argv)``  ,再去获取每个指令独有的OptionParser并且解析指令  ``init -u xxxx -b xxx`` 

OptionParser属性函数的代码如下：

{%highlight python linenos%}
class Command(object):
  """Base class for any command line action in repo.
  """
  ...
 @property
  def OptionParser(self):
    if self._optparse is None:
      try:
        me = 'repo %s' % self.NAME
        usage = self.helpUsage.strip().replace('%prog', me)
      except AttributeError:
        usage = 'repo %s' % self.NAME
      self._optparse = optparse.OptionParser(usage=usage)
      self._Options(self._optparse)
    return self._optparse
  ...
  def _Options(self, p):
    """Initialize the option parser.
    """
{%endhighlight%}
Command的衍生类重写了基类的_Options，定义了属于自己的options,先留个坑后面讲到"repo sync"的时候再分析。

创建完XmlManifest类，解析命令行后，接下来就是调用Execute。

&emsp;&emsp;Command类是所有命令（init、sync、start）的基类，其成员函数Execute被其衍生类重写，故调用成员函数Execute就可以执行某个命令对应的成员函数Execute。所以，执行到这一行  ``result = cmd.Execute(copts, cargs)``  的时候,就是整个架构的分水岭了。下面的图片是对前面的总结。

![repo _Repo#_Run flowchart]({{site.baseurl}}/asset/2017-04-12/2017-04-12-repo__Repo_Run_flowchart.png){:.white-bg-image}


接下来就是执行init模块中Init类的成员函数Execute：

{%highlight python linenos%}
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
{%endhighlight%}
&emsp;&emsp;Init类的成员函数Execute的重点在于两个成员函数_SyncManifest和_LinkManifest，前者会克隆出manifest仓库并且切换到可用的分支上，后者会通过os模块symlink函数生成链接文件manifest.xml。

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
&emsp;&emsp;Init类的成员函数_SyncManifest会克隆一个仓库，流程一般如下： ``git init--->git fetch--->git checkout branch_name``  。对应的Project类成员函数就是_InitGitDir，Sync_NetworkHalf，Sync_LocalHalf,是不是很熟悉，跟克隆repo仓库的流程是一样的，其实repo仓库、manifest仓库、projects仓库集这些仓库克隆出来的方式是一样的。


{%highlight python linenos%}
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
{%endhighlight%}

&emsp;&emsp;_InitGitDir，初始化的仓库为manifest.git,manifest目录下的.git仓库是manifest的复制品，通过Project类的成员函数_InitWorkTree创建。接着再说类_GitGetByExec，_GitGetByExec的对象bare_objdir封装了操作仓库的命令。比如git init。但是却找不到成员函数init，原来成员函数init是动态定义的。关键的地方就在于_GitGetByExec类的成员函数_getattr_。

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
            ...
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
          ...
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
&emsp;&emsp;runner闭包用来处理调用者提供的参数，比如bare_git.describe(project.GetRevisionId())中的"project.GetRevisionId()",对应的git命令就是  `` git  describe  args  ``
所以_GitGetByExec类通过成员函数__getattr__可以向工厂一样生产一些执行git命令的成员函数。既然仓库已经初始化好了，那么接下来就是fetch仓库了。

Sync_NetworkHalf成员函数的代码如下：

{%highlight python linenos%}
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
{%endhighlight%}

&emsp;&emsp;Project类Sync_NetworkHalf方法调用_RemoteFetch方法实现了从远程仓库fetch记录到本地仓库，_RemoteFetch函数其实是"git fetch"命令的封装。

Sync_LocalHalf成员函数的代码如下：

{%highlight python linenos%}
class Project(object):  
  ...

  def Sync_LocalHalf(self, syncbuf, force_sync=False):
    """Perform only the local IO portion of the sync process.
       Network access is not required.
    """
    self._InitWorkTree(force_sync=force_sync)
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

- _InitWorkTree成员函数：初始化manifest工作目录下的.git仓库
- _Checkout成员函数：通过"git checkout"切换分支。

_LinkManifest成员函数的代码如下：

{%highlight python linenos%}
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
{%endhighlight%}
&emsp;&emsp;成员函数_LinkManifest最终会调用os.symlink，创建manifest工作目录下default.xml的链接文件manifest.xml到 .repo目录下，这样方便访问manifest.xml文件

### *Projects仓库集*{:.header3-font}

&emsp;&emsp;执行完repo init就获取到了repo仓库和manifest仓库了，接下来就要通过manifest.xml链接文件中的AOSP各个项目的元数据，获取projects仓库集。先来看看其内容：

{%highlight xml %}
<?xml version="1.0" encoding="UTF-8"?>  
<manifest>  
  
  <remote  name="aosp"  
           fetch=".."  
           review="https://android-review.googlesource.com/" />  
  <default revision="refs/tags/android-4.2_r1"  
           remote="aosp"  
           sync-j="4" />  
  
  <project path="build" name="platform/build" >  
    <copyfile src="core/root.mk" dest="Makefile" />  
  </project>  
  <project path="abi/cpp" name="platform/abi/cpp" />  
  <project path="bionic" name="platform/bionic" />  
  ......  
  
</manifest> 
{%endhighlight%}
&emsp;&emsp;想了解更多的manifest.xml可以查看.repo/repo/docs/manifest-format.txt。这里我们只做简单了解
manifest.xml定义了四种标签：

- remote：该标签描述的是远程仓库信息。其中的fetch值相当于url路径的前缀。就好比 ``git@github.com:HawksJamesf/blog.git``  中的 ``git@github.com:`` ，标明了服务器。属性review用于code review服务器地址。
- default：属性revision表明了AOSP项目使用的开发分支，属性sync-j表明了拉取代码时使用的cpu核数
- project: 描述了相对于远程仓库的位置和相对于AOSP根目录的目录名字。比如想要获取build仓库，远程仓库的url为    ``https://android.googlesource.com/platform``，那么该仓库的对应的远程仓库的url就是   ``https://android.googlesource.com/platform/build``
- copyfile: 属性src为某个文件在远程仓库的位置，属性dest为本地仓库的位置。 

&emsp;&emsp;执行  `` repo sync -j 8  ``  命令行，流程就跟执行repo init是一样的，到了main模块里面的_Repo类的成员函数_Run调用cmd.Execute(copts, cargs)这个风水岭，才会执行属于sync模块的代码。但是关于copts，cargs参数的如何获取，我们还得先看cmd.OptionParser.parse_args(argv)。

_Options成员函数的代码如下：

{%highlight python linenos%}
class Sync(Command, MirrorSafeCommand):
  ...
  def _Options(self, p, show_smart=True):
    try:
      self.jobs = self.manifest.default.sync_j
    except ManifestParseError:
      self.jobs = 1

    ...
    p.add_option('-l', '--local-only',
                 dest='local_only', action='store_true',
                 help="only update working tree, don't fetch")
    p.add_option('-n', '--network-only',
                 dest='network_only', action='store_true',
                 help="fetch only, don't update working tree") 
    ...
    p.add_option('-m', '--manifest-name',
                 dest='manifest_name',
                 help='temporary manifest to use for this sync', metavar='NAME.xml')
    ...
    p.add_option('-u', '--manifest-server-username', action='store',
                 dest='manifest_server_username',
                 help='username to authenticate with the manifest server')
    p.add_option('-p', '--manifest-server-password', action='store',
                 dest='manifest_server_password',
                 help='password to authenticate with the manifest server')
    p.add_option('--fetch-submodules',
                 dest='fetch_submodules', action='store_true',
                 help='fetch submodules from server')
    ...
    
    if show_smart:
      p.add_option('-s', '--smart-sync',
                   dest='smart_sync', action='store_true',
                   help='smart sync using manifest from the latest known good build')
      p.add_option('-t', '--smart-tag',
                   dest='smart_tag', action='store',
                   help='smart sync using manifest from a known tag')

    g = p.add_option_group('repo Version options')
    g.add_option('--no-repo-verify',
                 dest='no_repo_verify', action='store_true',
                 help='do not verify repo source code')
    g.add_option('--repo-upgraded',
                 dest='repo_upgraded', action='store_true',
                 help=SUPPRESS_HELP)
{%endhighlight%}
&emsp;&emsp;在分析repo init时已经说用，Command的衍生类override成员函数_Options，才能得到独有的OptionParser。还记得  ``repo command line --->optparse--->git command line``这个流程吗 ? 每种命令都有其对应的OptionParser，这样才能做到各个命令模块有自己处理repo command line的逻辑。紧接着把解析后的值传给成员函数Execute。

Execute成员函数的代码如下：

{%highlight python linenos%}
class Sync(Command, MirrorSafeCommand):
  ...
  def Execute(self, opt, args):
    ...

    manifest_name = opt.manifest_name
    ...

    rp = self.manifest.repoProject
    rp.PreSync()

    mp = self.manifest.manifestProject
    mp.PreSync()

    ...

    if not opt.local_only:
      mp.Sync_NetworkHalf(quiet=opt.quiet,
                          current_branch_only=opt.current_branch_only,
                          no_tags=opt.no_tags,
                          optimized_fetch=opt.optimized_fetch)

    if mp.HasChanges:
      syncbuf = SyncBuffer(mp.config)
      mp.Sync_LocalHalf(syncbuf)
      if not syncbuf.Finish():
        sys.exit(1)
      self._ReloadManifest(manifest_name)
      if opt.jobs is None:
        self.jobs = self.manifest.default.sync_j
    ...
    all_projects = self.GetProjects(args,
                                    missing_ok=True,
                                    submodules_ok=opt.fetch_submodules)

    self._fetch_times = _FetchTimes(self.manifest)
    if not opt.local_only:
      to_fetch = []
      now = time.time()
      if _ONE_DAY_S <= (now - rp.LastFetch):
        to_fetch.append(rp)
      to_fetch.extend(all_projects)
      to_fetch.sort(key=self._fetch_times.Get, reverse=True)

      fetched = self._Fetch(to_fetch, opt)
      _PostRepoFetch(rp, opt.no_repo_verify)
      if opt.network_only:
        # bail out now; the rest touches the working tree
        return

      # Iteratively fetch missing and/or nested unregistered submodules
      previously_missing_set = set()
      while True:
        ...
        all_projects = self.GetProjects(args,
                                        missing_ok=True,
                                        submodules_ok=opt.fetch_submodules)
        missing = []
        for project in all_projects:
          if project.gitdir not in fetched:
            missing.append(project)
        if not missing:
          break
        # Stop us from non-stopped fetching actually-missing repos: If set of
        # missing repos has not been changed from last fetch, we break.
        missing_set = set(p.name for p in missing)
        if previously_missing_set == missing_set:
          break
        previously_missing_set = missing_set
        fetched.update(self._Fetch(missing, opt))

    ...

    if self.UpdateProjectList():
      sys.exit(1)

    ...
    for project in all_projects:
      ...
      if project.worktree:
        project.Sync_LocalHalf(syncbuf, force_sync=opt.force_sync)
    ...

    ...
{%endhighlight%}
&emsp;&emsp;前期会有一些更新检查repo仓库和manifest仓库的工作，后期就会拉去projects仓库集，那么下面我们就来粗糙的理解执行成员函数Execute的流程：

- 一开始获取manifest仓库和repo仓库的对象，然后都会调用之前分析过的PreSync，如果opt.local_only不存在，就会调用Sync_NetworkHalf成员函数更新manifest仓库。紧接着如果manifest本地仓库相对于远程仓库有变化，就会调用Sync_LocalHalf做一些merge或者rebase操作，然后调用ReloadManifest成员函数重新从manifest.xml载入数据到对象。
- 接下来就是_Fetch成员函数，其中除了manifest仓库，其他的仓库都会更新。如果开启的合数大于1的话就会创建新的线程，防止主线程阻塞，其中关于线程同步机制可以查看[这里](http://www.laurentluce.com/posts/python-threads-synchronization-locks-rlocks-semaphores-conditions-events-and-queues/)。而获取projects仓库集，主要使用的是Project类的成员函数Sync_NetworkHalf，接着调用_PostRepoFetch函数判断repo仓库是否有变化，如果是，则调用Sync_LocalHalf成员函数做一些merge或者rebase操作。
- 紧接着通过GetProjects成员函数从 .repo/projects目录下得到AOSP所有仓库对象的列表，不包括repo仓库和manifest仓库，这样就可以调用Sync_LocalHalf成员函数。如果参数args指定了具体的仓库（即repo sync project_name），那么GetProjects成员函数就只能得到指定的仓库。获取仓库的方式有两种：一种_GetProjectByPath，另一种是GetProjectsWithName。

&emsp;&emsp;至此，repo仓库、manifest仓库、projects仓库集连同其对应的工作目录都已经初始化完成。那么是不是就可以开始开发呢 ？ 其实接下来还要为AOSP项目的仓库创建一个新的开发分支，只有这样我们才能够在分支上面提交、上传自己的代码。也只有这样当我们发布了一个版本就可以给这个版本打上一个tag。当项目可以量产时，就可以在这个分支基础上创建出一个量产分支，并上传到服务器。

### *创建分支*{:.header3-font}
``repo start master --all`` 其实挺好理解这个命令行的，就是  ``git checkout -b name`` 命令行的批量操作。留个坑，以后填吧。

{%highlight python linenos%}
class Start(Command):
  ...
  def _Options(self, p):
    p.add_option('--all',
                 dest='all', action='store_true',
                 help='begin branch in all projects')

  def Execute(self, opt, args):
    if not args:
      self.Usage()

    nb = args[0]
    if not git.check_ref_format('heads/%s' % nb):
      print("error: '%s' is not a valid name" % nb, file=sys.stderr)
      sys.exit(1)

    err = []
    projects = []
    if not opt.all:
      projects = args[1:]
      if len(projects) < 1:
        projects = ['.',]  # start it in the local project by default

    all_projects = self.GetProjects(projects,
                                    missing_ok=bool(self.gitc_manifest))

    # This must happen after we find all_projects, since GetProjects may need
    # the local directory, which will disappear once we save the GITC manifest.
    if self.gitc_manifest:
      gitc_projects = self.GetProjects(projects, manifest=self.gitc_manifest,
                                       missing_ok=True)
      for project in gitc_projects:
        if project.old_revision:
          project.already_synced = True
        else:
          project.already_synced = False
          project.old_revision = project.revisionExpr
        project.revisionExpr = None
      # Save the GITC manifest.
      gitc_utils.save_manifest(self.gitc_manifest)

      # Make sure we have a valid CWD
      if not os.path.exists(os.getcwd()):
        os.chdir(self.manifest.topdir)

    pm = Progress('Starting %s' % nb, len(all_projects))
    for project in all_projects:
      pm.update()

      if self.gitc_manifest:
        gitc_project = self.gitc_manifest.paths[project.relpath]
        # Sync projects that have not been opened.
        if not gitc_project.already_synced:
          proj_localdir = os.path.join(self.gitc_manifest.gitc_client_dir,
                                       project.relpath)
          project.worktree = proj_localdir
          if not os.path.exists(proj_localdir):
            os.makedirs(proj_localdir)
          project.Sync_NetworkHalf()
          sync_buf = SyncBuffer(self.manifest.manifestProject.config)
          project.Sync_LocalHalf(sync_buf)
          project.revisionId = gitc_project.old_revision

      # If the current revision is a specific SHA1 then we can't push back
      # to it; so substitute with dest_branch if defined, or with manifest
      # default revision instead.
      branch_merge = ''
      if IsId(project.revisionExpr):
        if project.dest_branch:
          branch_merge = project.dest_branch
        else:
          branch_merge = self.manifest.default.revisionExpr

      if not project.StartBranch(nb, branch_merge=branch_merge):
        err.append(project)
    pm.end()

    if err:
      for p in err:
        print("error: %s/: cannot start %s" % (p.relpath, nb),
              file=sys.stderr)
      sys.exit(1)
{%endhighlight%}



## *4.Reference*{:.header2-font}
[Android Open Source Project](https://source.android.com/source/developing)
[repo仓库源码](https://github.com/HawksJamesf/python-experimental)
[清华大学提供的AOSP](https://mirrors.tuna.tsinghua.edu.cn/help/AOSP/)
[Android源代码仓库及其管理工具Repo分析](http://blog.csdn.net/luoshengyang/article/details/18195205)

