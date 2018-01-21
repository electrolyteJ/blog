---
layout: post
title:  构建工具GNU make
description: 使用Makefile语言描述编译过程
date: 2017-10-11
share: true
comments: true
tag:
- Build Tools
# - AOSP(SYS)
---
## *1.Summary*{:.header2-font}
&emsp;&emsp;在阅读GNU make构建工具相关资料的时候，一直在思考几个问题，
- “ build system ” 是翻译成构建系统还是编译系统 ？
- make是什么 ？ make可能是构建系统，make也可能是是构建系统中的一部分构建工具。
-  make的使用场景 ？

&emsp;&emsp;其实如果不回答上面三个问题，并不会对我们学习Makefile语言有什么障碍。但是笔者个性使然，就是想要把这些关系梳理清楚再去学习其中的语法。

&emsp;&emsp;先来回答第一个问题，阮一峰在他的博文中认为build叫做构建，compile叫做编译，参考这个[Make 命令教程](http://www.ruanyifeng.com/blog/2015/02/make.html)。所以我认为“ build system ” 叫做构建系统，而构建工具是构建系统中的一部分。构建工具有很多种 ：成熟大型项目常用的make ，Android平台开发应用的gradle ，人工智能TensorFlow的bazel。

&emsp;&emsp;那么接下来回答第二个问题，make是什么 ？make是构建系统中的一部分，是一种构建工具。用于规划如何编译项目。就好比汽车制造厂的组装器，调配汽车的各个零部件资源，并且进行合理的组装形成一辆完整的汽车。由于平台不同编译器不同等原因，它分为好多种 ：GNU make，Visual C++的nmake ，cmake ，qmake 。想了解其差异，可以参考这个[make makefile cmake qmake都是什么，有什么区别？](https://www.zhihu.com/question/27455963) 

&emsp;&emsp;最后回答第三个问题，make相对于其他构建工具的历史来的悠久，其稳定性自然不言而喻。它是c/c++项目的必备工具，由于c/c++的语言特性导致很多大型项目的底层都离不开它，致使像“ Android Open Source Project ”这样的大型项目使用make来完成这个系统的编译、打包等工作 。就连阮一峰也在博文中推荐使用make来构建Node.js这种大型项目，参考这个[使用 Make 构建网站](http://www.ruanyifeng.com/blog/2015/03/build-website-with-make.html)
## *2.About*{:.header2-font}
&emsp;&emsp;make是一个构建工具，我们要书写Makefile文件，才能让这个工具按照规则执行，所以讲解Makefile是这篇文章的核心。本文是GNU make，所以Makefile语言格式跟其他的make工具有点区别，不过我们主要是了解其精髓，掌握GNU make也就自然会达到触类旁通的效果。
## *3.Intoduction*{:.header2-font}
&emsp;&emsp;想要快速学习make这个构建工具，就需要从“熟悉Makefile的语法”和“Makefile在大型项目的使用“这两个方面来入手。

### **初步认识Makefile语言**{:.header3-font}
&emsp;&emsp;如果是有ROM工作经验的工程师一定用过``make snod``这条命令.它会重新打包生成system.img。执行`make snod`后经过一系列的流程到达下面的代码。

build/core/Makefile
{%highlight makefile%}
 .PHONY: systemimage-nodeps snod
 systemimage-nodeps snod: $(filter-out systemimage-nodeps snod,$(MAKECMDGOALS)) \
                     | $(INTERNAL_USERIMAGES_DEPS)
         @echo "make $@: ignoring dependencies"
         $(call build-systemimage-target,$(INSTALLED_SYSTEMIMAGE))
         $(hide) $(call assert-max-image-size,$(INSTALLED_SYSTEMIMAGE),$(BOARD_SYSTEMIMAGE_PARTITION_SIZE))
{%endhighlight%}

&emsp;&emsp;上面的代码基本说明了Makefile语言的使用。snod是一个标识，也是一个伪目标（phony target），与之相对的就是目标，是一个文件（目标文件、可执行文件）。而冒号右边，是左边的预备条件。他们的下一行就是编译指令或者是控制指令。比如这样
{%highlight makefile%}
main: main.o
    gcc ... #编译生成main文件
main.o:main.c main.h
    gcc ... #编译生成main.o
{%endhighlight%}
&emsp;&emsp;这个就是一个规则（rule），定义了如何编译的规则。可以用一个通用公式来表达，就是下面这个

```
target … : prerequisites …
[ TAB ]recipe
[ TAB ]…
[ TAB ]…
```

&emsp;&emsp;当然Makefile语言也会有变量、函数。这个文章就不详细讲解Makefile语法了，因为已经有好多人都写过相关的文章，可以参考权威的”[GNU make](http://www.gnu.org/software/make/manual/html_node/index.html?cm_mc_uid=45784307156114982261855&cm_mc_sid_50200000=1506734444)“,如果看不懂英文或者看英文吃力，可以参考这个中文文章”[跟我一起写Makefile](http://wiki.ubuntu.org.cn/%E8%B7%9F%E6%88%91%E4%B8%80%E8%B5%B7%E5%86%99Makefile)“。还有我最喜欢的博主老罗对Makefile的理解“[Android编译系统简要介绍和学习计划](http://blog.csdn.net/luoshengyang/article/details/18466779)”

### **make在Android平台的运用**{:.header3-font}
&emsp;&emsp;为了加快AOSP项目的编译速度，Android团队在N版本添加了ninja构建工具，ninja构建工具相对于make构建工具更底层。通过开源项目kati(kati是项目名，但是最终编译生成的程序名却是叫做ckati，后续我们将使用ckati这个名字)将Makefile文件翻译成ninja文件。make和ninja的关系就像cmake和make。还有一点要注意的，由于7.1以后部分使用的是Soong+Buleprint这套构建工具，将bp文件转换成ninja文件，所以Makefile文件和Buleprint文件是混合使用的，分析Makefile文件要小心一点。不过Blueprint+Soong这套构建工具代替make、kati这套构建工具只是时间问题。想了解Buleprint+Soong这套构建工具可以参考这一篇[Android源码解析之AOSP新的构建系统]({{site.baseurl}}/blog/2017-09-23/2017-09-23-translate-blueprint-soong)。 那么我们就来大致了解一下这个转换的流程

build/core/main.mk
{%highlight makefile %}
...
ifndef KATI

host_prebuilts := linux-x86
ifeq ($(shell uname),Darwin)
host_prebuilts := darwin-x86
endif

.PHONY: run_soong_ui
run_soong_ui:
	+@prebuilts/build-tools/$(host_prebuilts)/bin/makeparallel --ninja build/soong/soong_ui.bash --make-mode $(MAKECMDGOALS)

.PHONY: $(MAKECMDGOALS)
$(sort $(MAKECMDGOALS)) : run_soong_ui
	@#empty

else #KATI 
... 
endif #KATI 
{%endhighlight%}

&emsp;&emsp;当我们在项目顶级目录执行make命令时，在顶级目录有个Makefile文件include build/core/main.mk。所以主要的内容都在main.mk这个文件里面。由于KATI一开始并没有定义，所以会执行`+@prebuilts/build-tools/$(host_prebuilts)/bin/makeparallel --ninja build/soong/soong_ui.bash --make-mode $(MAKECMDGOALS)`语句。makeparallel程序会fork出一个子进程执行soong_ui.bash，参数为`--make-mode $(MAKECMDGOALS)`。soong_ui.bash也很简单，就是执行soong_ui程序，该程序使用go语言写的。

我们来看看入库文件main.go
build/core/soong/cmd/soong_ui/main.go
{%highlight go %}
func main() {
	...

	build.Build(buildCtx, config, build.BuildAll)
}
{%endhighlight%}

build文件中Build函数就是执行ckati或者ninja程序的关键函数,

build/core/soong/ui/build/build.go
{%highlight go %}
...

const (
	BuildNone          = iota
	BuildProductConfig = 1 << iota
	BuildSoong         = 1 << iota
	BuildKati          = 1 << iota
	BuildNinja         = 1 << iota
	BuildAll           = BuildProductConfig | BuildSoong | BuildKati | BuildNinja
)

func Build(ctx Context, config Config, what int) {
	ctx.Verboseln("Starting build with args:", config.Arguments())
	ctx.Verboseln("Environment:", config.Environment().Environ())

	if inList("help", config.Arguments()) {
		cmd := exec.CommandContext(ctx.Context, "make", "-f", "build/core/help.mk")
		cmd.Env = config.Environment().Environ()
		cmd.Stdout = ctx.Stdout()
		cmd.Stderr = ctx.Stderr()
		if err := cmd.Run(); err != nil {
			ctx.Fatalln("Failed to run make:", err)
		}
		return
	}

	SetupOutDir(ctx, config)

	if what&BuildProductConfig != 0 {
		// Run make for product config
		runMakeProductConfig(ctx, config)
	}

	if what&BuildSoong != 0 {
		// Run Soong
		runSoongBootstrap(ctx, config)
		runSoong(ctx, config)
	}

	if what&BuildKati != 0 {
		// Run ckati
		runKati(ctx, config)
	}

	if what&BuildNinja != 0 {
		// Write combined ninja file
		createCombinedBuildNinjaFile(ctx, config)

		// Run ninja
		runNinja(ctx, config)
	}
}
{%endhighlight%}
&emsp;&emsp;从main.go传过来的what参数为build.BuildAll，而BuildAll在build.go的定义就可以知道Build函数会一次执行run make、run Soong、run ckati、run ninja。每个工具的使用对应着一个go文件，比如run make，有make.go;run soong ，有soong.go。但是只有在run ckati时，ckati工具会再次执行build/core/main.mk文件。为什么要在这里执行main.mk，我们后面会讲到。先来看看看ckati的调用逻辑

build/soong/ui/build
{%highlight go linenos%}

...

func runKati(ctx Context, config Config) {
	ctx.BeginTrace("kati")
	defer ctx.EndTrace()

	genKatiSuffix(ctx, config)

	executable := "prebuilts/build-tools/" + config.HostPrebuiltTag() + "/bin/ckati"
	args := []string{
		"--ninja",
		"--ninja_dir=" + config.OutDir(),
		"--ninja_suffix=" + config.KatiSuffix(),
		"--regen",
		"--ignore_optional_include=" + filepath.Join(config.OutDir(), "%.P"),
		"--detect_android_echo",
		"--color_warnings",
		"--gen_all_targets",
		"-f", "build/core/main.mk",
	}

	if !config.Environment().IsFalse("KATI_EMULATE_FIND") {
		args = append(args, "--use_find_emulator")
	}

	args = append(args, config.KatiArgs()...)

	args = append(args,
		"BUILDING_WITH_NINJA=true",
		"SOONG_ANDROID_MK="+config.SoongAndroidMk(),
		"SOONG_MAKEVARS_MK="+config.SoongMakeVarsMk())

	if config.UseGoma() {
		args = append(args, "-j"+strconv.Itoa(config.Parallel()))
	}

	cmd := exec.CommandContext(ctx.Context, executable, args...)
	...
}

...

{%endhighlight%}

&emsp;&emsp;很简单的几句话，就是执行ckati命令。


build/kati/main.cc
{%highlight cpp linenos%}

...

int main(int argc, char* argv[]) {
  if (argc >= 2 && !strcmp(argv[1], "--realpath")) {
    HandleRealpath(argc - 2, argv + 2);
    return 0;
  }
  Init();
  string orig_args;
  for (int i = 0; i < argc; i++) {
    if (i)
      orig_args += ' ';
    orig_args += argv[i];
  }
  g_flags.Parse(argc, argv);
  FindFirstMakefie();
  if (g_flags.makefile == NULL)
    ERROR("*** No targets specified and no makefile found.");
  // This depends on command line flags.
  if (g_flags.use_find_emulator)
    InitFindEmulator();
  int r = Run(g_flags.targets, g_flags.cl_vars, orig_args);
  Quit();
  return r;
}

{%endhighlight%}

&emsp;&emsp;对于ckati命令的解析，我们只要看`g_flags.Parse(argc, argv);`,g_flags是一个拥有Parse方法的结构体变量


build/kati/flags.cc
{%highlight cpp linenos%}

...

void Flags::Parse(int argc, char** argv) {
  subkati_args.push_back(argv[0]);
  num_jobs = num_cpus = sysconf(_SC_NPROCESSORS_ONLN);
  const char* num_jobs_str;

  if (const char* makeflags = getenv("MAKEFLAGS")) {
    for (StringPiece tok : WordScanner(makeflags)) {
      if (!HasPrefix(tok, "-") && tok.find('=') != string::npos)
        cl_vars.push_back(tok);
    }
  }

  for (int i = 1; i < argc; i++) {
    const char* arg = argv[i];
    bool should_propagate = true;
    int pi = i;
    if (!strcmp(arg, "-f")) {
      makefile = argv[++i];
      should_propagate = false;
    } else if (!strcmp(arg, "-c")) {
      is_syntax_check_only = true;
    } else if (!strcmp(arg, "-i")) {
      is_dry_run = true;
    } else if (!strcmp(arg, "-s")) {
      is_silent_mode = true;
    } else if (!strcmp(arg, "-d")) {
      enable_debug = true;
    } else if (!strcmp(arg, "--kati_stats")) {
      enable_stat_logs = true;
    } else if (!strcmp(arg, "--warn")) {
      enable_kati_warnings = true;
    } else if (!strcmp(arg, "--ninja")) {
      generate_ninja = true;
    } else if (!strcmp(arg, "--gen_all_targets")) {
      gen_all_targets = true;
    } else if (!strcmp(arg, "--regen")) {
      // TODO: Make this default.
      regen = true;
    } else if (!strcmp(arg, "--regen_debug")) {
      regen_debug = true;
    } else if (!strcmp(arg, "--regen_ignoring_kati_binary")) {
      regen_ignoring_kati_binary = true;
    } else if (!strcmp(arg, "--dump_kati_stamp")) {
      dump_kati_stamp = true;
      regen_debug = true;
    } else if (!strcmp(arg, "--detect_android_echo")) {
      detect_android_echo = true;
    } else if (!strcmp(arg, "--detect_depfiles")) {
      detect_depfiles = true;
    } else if (!strcmp(arg, "--color_warnings")) {
      color_warnings = true;
    } else if (ParseCommandLineOptionWithArg(
        "-j", argv, &i, &num_jobs_str)) {
      num_jobs = strtol(num_jobs_str, NULL, 10);
      if (num_jobs <= 0) {
        ERROR("Invalid -j flag: %s", num_jobs_str);
      }
    } else if (ParseCommandLineOptionWithArg(
        "--remote_num_jobs", argv, &i, &num_jobs_str)) {
      remote_num_jobs = strtol(num_jobs_str, NULL, 10);
      if (remote_num_jobs <= 0) {
        ERROR("Invalid -j flag: %s", num_jobs_str);
      }
    } else if (ParseCommandLineOptionWithArg(
        "--ninja_suffix", argv, &i, &ninja_suffix)) {
    } else if (ParseCommandLineOptionWithArg(
        "--ninja_dir", argv, &i, &ninja_dir)) {
    } else if (!strcmp(arg, "--use_find_emulator")) {
      use_find_emulator = true;
    } else if (ParseCommandLineOptionWithArg(
        "--goma_dir", argv, &i, &goma_dir)) {
    } else if (ParseCommandLineOptionWithArg(
        "--ignore_optional_include",
        argv, &i, &ignore_optional_include_pattern)) {
    } else if (ParseCommandLineOptionWithArg(
        "--ignore_dirty",
        argv, &i, &ignore_dirty_pattern)) {
    } else if (ParseCommandLineOptionWithArg(
        "--no_ignore_dirty",
        argv, &i, &no_ignore_dirty_pattern)) {
    } else if (arg[0] == '-') {
      ERROR("Unknown flag: %s", arg);
    } else {
      if (strchr(arg, '=')) {
        cl_vars.push_back(arg);
      } else {
        should_propagate = false;
        targets.push_back(Intern(arg));
      }
    }

    if (should_propagate) {
      for (; pi <= i; pi++) {
        subkati_args.push_back(argv[pi]);
      }
    }
  }
}
{%endhighlight%}

&emsp;&emsp;这里我们可以看到对于命令的解析，解析完之后，开始了main.cc中的Run函数。

build/kati/main.cc
{%highlight cpp linenos%}

...

static int Run(const vector<Symbol>& targets,
               const vector<StringPiece>& cl_vars,
               const string& orig_args) {
  double start_time = GetTime();

  if (g_flags.generate_ninja && (g_flags.regen || g_flags.dump_kati_stamp)) {
    ScopedTimeReporter tr("regen check time");
    if (!NeedsRegen(start_time, orig_args)) {
      fprintf(stderr, "No need to regenerate ninja file\n");
      return 0;
    }
    if (g_flags.dump_kati_stamp) {
      printf("Need to regenerate ninja file\n");
      return 0;
    }
    ClearGlobCache();
  }

  SetAffinityForSingleThread();

  MakefileCacheManager* cache_mgr = NewMakefileCacheManager();

  Intern("MAKEFILE_LIST").SetGlobalVar(
      new SimpleVar(StringPrintf(" %s", g_flags.makefile), VarOrigin::FILE));
  for (char** p = environ; *p; p++) {
    SetVar(*p, VarOrigin::ENVIRONMENT);
  }
  Evaluator* ev = new Evaluator();

  vector<Stmt*> bootstrap_asts;
  ReadBootstrapMakefile(targets, &bootstrap_asts);
  ev->set_is_bootstrap(true);
  for (Stmt* stmt : bootstrap_asts) {
    LOG("%s", stmt->DebugString().c_str());
    stmt->Eval(ev);
  }
  ev->set_is_bootstrap(false);

  ev->set_is_commandline(true);
  for (StringPiece l : cl_vars) {
    vector<Stmt*> asts;
    Parse(Intern(l).str(), Loc("*bootstrap*", 0), &asts);
    CHECK(asts.size() == 1);
    asts[0]->Eval(ev);
  }
  ev->set_is_commandline(false);

  {
    ScopedTimeReporter tr("eval time");
    Makefile* mk = cache_mgr->ReadMakefile(g_flags.makefile);
    for (Stmt* stmt : mk->stmts()) {
      LOG("%s", stmt->DebugString().c_str());
      stmt->Eval(ev);
    }
  }

  for (ParseErrorStmt* err : GetParseErrors()) {
    WARN_LOC(err->loc(), "warning for parse error in an unevaluated line: %s",
             err->msg.c_str());
  }

  vector<DepNode*> nodes;
  {
    ScopedTimeReporter tr("make dep time");
    MakeDep(ev, ev->rules(), ev->rule_vars(), targets, &nodes);
  }

  if (g_flags.is_syntax_check_only)
    return 0;

  if (g_flags.generate_ninja) {
    ScopedTimeReporter tr("generate ninja time");
    GenerateNinja(nodes, ev, orig_args, start_time);
    return 0;
  }

  for (const auto& p : ev->exports()) {
    const Symbol name = p.first;
    if (p.second) {
      Var* v = ev->LookupVar(name);
      const string&& value = v->Eval(ev);
      LOG("setenv(%s, %s)", name.c_str(), value.c_str());
      setenv(name.c_str(), value.c_str(), 1);
    } else {
      LOG("unsetenv(%s)", name.c_str());
      unsetenv(name.c_str());
    }
  }

  {
    ScopedTimeReporter tr("exec time");
    Exec(nodes, ev);
  }

  for (Stmt* stmt : bootstrap_asts)
    delete stmt;
  delete ev;
  delete cache_mgr;

  return 0;
}
...
{%endhighlight%}

&emsp;&emsp;Run函数会将Makefile文件翻译成ninja文件。由于这一篇文章的重心不是ckati源码的分析，所以有兴趣的话可以参考这一篇[Android7.0 Ninja编译原理](http://blog.csdn.net/chaoy1116/article/details/53063082)。ninja文件已经有啦，接下来就是执行ninja工具了。

&emsp;&emsp;之前讲到kati.go文件中调用ckati有一个重要的参数`-f build/core/main.mk` ，也就是生成ninja文件之后会执行main.mk。之前说过为什么build/core/main.mk会在run ckati流程执行？现在我们就来回答这个问题。先来看看main.mk文件的内容

build/core/main.mk
{%highlight makefile %}
...
ifndef KATI
... #1流程
else #KATI 
... #2流程
endif #KATI 
{%endhighlight%}

&emsp;&emsp;最初使用make命令，由于KATI没有定义，走的是1流程。由于执行ckati时，会导入环境变量KATI，所以当第二次执行main.mk文件，就会执行2流程。由于前期工作都准备好了，所以接下来就要开始使用ninja工具进行编译。

------

&emsp;&emsp;接下来我们就来看看后面的流程 

build/core/main.mk
{%highlight makefile linenos%}
...

ifndef KATI

...

else # KATI

# Absolute path of the present working direcotry.
# This overrides the shell variable $PWD, which does not necessarily points to
# the top of the source tree, for example when "make -C" is used in m/mm/mmm.
PWD := $(shell pwd)

TOP := .
TOPDIR :=

BUILD_SYSTEM := $(TOPDIR)build/core

# This is the default target.  It must be the first declared target.
.PHONY: droid
DEFAULT_GOAL := droid
$(DEFAULT_GOAL): droid_targets

.PHONY: droid_targets
droid_targets:

# Set up various standard variables based on configuration
# and host information.
include $(BUILD_SYSTEM)/config.mk

ifneq ($(filter $(dont_bother_goals), $(MAKECMDGOALS)),)
dont_bother := true
endif

include $(SOONG_MAKEVARS_MK)

include $(BUILD_SYSTEM)/clang/config.mk

# Write the build number to a file so it can be read back in
# without changing the command line every time.  Avoids rebuilds
# when using ninja.
$(shell mkdir -p $(OUT_DIR) && \
    echo -n $(BUILD_NUMBER) > $(OUT_DIR)/build_number.txt && \
    echo -n $(BUILD_DATETIME) > $(OUT_DIR)/build_date.txt)
BUILD_NUMBER_FROM_FILE := $$(cat $(OUT_DIR)/build_number.txt)
BUILD_DATETIME_FROM_FILE := $$(cat $(OUT_DIR)/build_date.txt)
...

# This allows us to force a clean build - included after the config.mk
# environment setup is done, but before we generate any dependencies.  This
# file does the rm -rf inline so the deps which are all done below will
# be generated correctly
include $(BUILD_SYSTEM)/cleanbuild.mk

...

ifneq ($(VERSION_CHECK_SEQUENCE_NUMBER)$(JAVA_NOT_REQUIRED),$(VERSIONS_CHECKED)$(JAVA_NOT_REQUIRED_CHECKED))

    $(info Checking build tools versions...)

    # check for a case sensitive file system
    ...

    # Make sure that there are no spaces in the absolute path; the
    # build system can't deal with them.
    ...

    ifneq ($(JAVA_NOT_REQUIRED),true)
        java_version_str := $(shell unset _JAVA_OPTIONS && java -version 2>&1)
        javac_version_str := $(shell unset _JAVA_OPTIONS && javac -version 2>&1)

        # Check for the correct version of java, should be 1.8 by
        # default and only 1.7 if LEGACY_USE_JAVA7 is set.
        ...

        # Check for the current JDK.
        #
        # For Java 1.7/1.8, we require OpenJDK on linux and Oracle JDK on Mac OS.
        requires_openjdk := false
        ifeq ($(BUILD_OS),linux)
        requires_openjdk := true
        endif


        # Check for the current jdk
        ...

        KNOWN_INCOMPATIBLE_JAVAC_VERSIONS := google
        incompat_javac := $(foreach v,$(KNOWN_INCOMPATIBLE_JAVAC_VERSIONS),$(findstring $(v),$(javac_version_str)))
        ifneq ($(incompat_javac),)
        javac_version :=
        endif

        # Check for the correct version of javac
        ...

    endif # if JAVA_NOT_REQUIRED

    ifndef BUILD_EMULATOR
    # Emulator binaries are now provided under prebuilts/android-emulator/
    BUILD_EMULATOR := false
    endif

    $(shell echo 'VERSIONS_CHECKED := $(VERSION_CHECK_SEQUENCE_NUMBER)' \
            > $(OUT_DIR)/versions_checked.mk)
    $(shell echo 'BUILD_EMULATOR ?= $(BUILD_EMULATOR)' \
            >> $(OUT_DIR)/versions_checked.mk)
    $(shell echo 'JAVA_NOT_REQUIRED_CHECKED := $(JAVA_NOT_REQUIRED)' \
            >> $(OUT_DIR)/versions_checked.mk)
endif

# These are the modifier targets that don't do anything themselves, but
# change the behavior of the build.
# (must be defined before including definitions.make)
INTERNAL_MODIFIER_TARGETS := showcommands all

# EMMA_INSTRUMENT_STATIC merges the static emma library to each emma-enabled module.
ifeq (true,$(EMMA_INSTRUMENT_STATIC))
EMMA_INSTRUMENT := true
endif

...

#
# -----------------------------------------------------------------
# Add the product-defined properties to the build properties.
ifdef PRODUCT_SHIPPING_API_LEVEL
ADDITIONAL_BUILD_PROPERTIES += \
  ro.product.first_api_level=$(PRODUCT_SHIPPING_API_LEVEL)
endif

ifneq ($(BOARD_PROPERTY_OVERRIDES_SPLIT_ENABLED), true)
  ADDITIONAL_BUILD_PROPERTIES += $(PRODUCT_PROPERTY_OVERRIDES)
else
  ifndef BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE
    ADDITIONAL_BUILD_PROPERTIES += $(PRODUCT_PROPERTY_OVERRIDES)
  endif
endif


# Bring in standard build system definitions.
include $(BUILD_SYSTEM)/definitions.mk

# Bring in dex_preopt.mk
include $(BUILD_SYSTEM)/dex_preopt.mk

...

# -----------------------------------------------------------------
# Variable to check java support level inside PDK build.
# Not necessary if the components is not in PDK.
# not defined : not supported
# "sdk" : sdk API only
# "platform" : platform API supproted
TARGET_BUILD_JAVA_SUPPORT_LEVEL := platform

# -----------------------------------------------------------------
# The pdk (Platform Development Kit) build
include build/core/pdk_config.mk

#
# -----------------------------------------------------------------
# Jack version configuration
-include $(TOPDIR)prebuilts/sdk/tools/jack_versions.mk
-include $(TOPDIR)prebuilts/sdk/tools/jack_for_module.mk

#
# -----------------------------------------------------------------
# Install and start Jack server
-include $(TOPDIR)prebuilts/sdk/tools/jack_server_setup.mk

#
# -----------------------------------------------------------------
# Jacoco package name for Jack
-include $(TOPDIR)external/jacoco/config.mk

....

# -----------------------------------------------------------------
###
### In this section we set up the things that are different
### between the build variants
###

is_sdk_build :=

ifneq ($(filter sdk win_sdk sdk_addon,$(MAKECMDGOALS)),)
is_sdk_build := true
endif

# Add build properties for ART. These define system properties used by installd
# to pass flags to dex2oat.
...

## user/userdebug ##

user_variant := $(filter user userdebug,$(TARGET_BUILD_VARIANT))
enable_target_debugging := true
tags_to_install :=
ifneq (,$(user_variant))
  ...

else # !user_variant
  ...
endif # !user_variant

ifeq (true,$(strip $(enable_target_debugging)))
  # Target is more debuggable and adbd is on by default
  ADDITIONAL_DEFAULT_PROPERTIES += ro.debuggable=1
  # Enable Dalvik lock contention logging.
  ADDITIONAL_BUILD_PROPERTIES += dalvik.vm.lockprof.threshold=500
  # Include the debugging/testing OTA keys in this build.
  INCLUDE_TEST_OTA_KEYS := true
else # !enable_target_debugging
  # Target is less debuggable and adbd is off by default
  ADDITIONAL_DEFAULT_PROPERTIES += ro.debuggable=0
endif # !enable_target_debugging

## eng ##

ifeq ($(TARGET_BUILD_VARIANT),eng)
...
endif

## sdk ##

ifdef is_sdk_build

...
else # !sdk
endif

...

#
# Typical build; include any Android.mk files we can find.
#

FULL_BUILD := true

# Before we go and include all of the module makefiles, mark the PRODUCT_*
# and ADDITIONAL*PROPERTIES values readonly so that they won't be modified.
$(call readonly-product-vars)
ADDITIONAL_DEFAULT_PROPERTIES := $(strip $(ADDITIONAL_DEFAULT_PROPERTIES))
.KATI_READONLY := ADDITIONAL_DEFAULT_PROPERTIES
ADDITIONAL_BUILD_PROPERTIES := $(strip $(ADDITIONAL_BUILD_PROPERTIES))
.KATI_READONLY := ADDITIONAL_BUILD_PROPERTIES

ifneq ($(PRODUCT_ENFORCE_RRO_TARGETS),)
ENFORCE_RRO_SOURCES :=
endif

ifneq ($(ONE_SHOT_MAKEFILE),)
# We've probably been invoked by the "mm" shell function
# with a subdirectory's makefile.
include $(SOONG_ANDROID_MK) $(wildcard $(ONE_SHOT_MAKEFILE))
...

else # ONE_SHOT_MAKEFILE

ifneq ($(dont_bother),true)
#
# Include all of the makefiles in the system
#

...

endif # dont_bother

endif # ONE_SHOT_MAKEFILE

# -------------------------------------------------------------------
# All module makefiles have been included at this point.
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Enforce to generate all RRO packages for modules having resource
# overlays.
# -------------------------------------------------------------------
ifneq ($(PRODUCT_ENFORCE_RRO_TARGETS),)
$(call generate_all_enforce_rro_packages)
endif

...

# -------------------------------------------------------------------
# Figure out our module sets.
#
# Of the modules defined by the component makefiles,
# determine what we actually want to build.

###########################################################
## Expand a module name list with REQUIRED modules
###########################################################
# $(1): The variable name that holds the initial module name list.
#       the variable will be modified to hold the expanded results.
# $(2): The initial module name list.
# Returns empty string (maybe with some whitespaces).
define expand-required-modules
$(eval _erm_new_modules := $(sort $(filter-out $($(1)),\
  $(foreach m,$(2),$(ALL_MODULES.$(m).REQUIRED)))))\
$(if $(_erm_new_modules),$(eval $(1) += $(_erm_new_modules))\
  $(call expand-required-modules,$(1),$(_erm_new_modules)))
endef

ifdef FULL_BUILD
  # The base list of modules to build for this product is specified
  # by the appropriate product definition file, which was included
  # by product_config.mk.
  ...
else
  # We're not doing a full build, and are probably only including
  # a subset of the module makefiles.  Don't try to build any modules
  # requested by the product, because we probably won't have rules
  # to build them.
  product_FILES :=
endif

eng_MODULES := $(sort \
        $(call get-tagged-modules,eng) \
        $(call module-installed-files, $(PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_PACKAGES_ENG)) \
    )
debug_MODULES := $(sort \
        $(call get-tagged-modules,debug) \
        $(call module-installed-files, $(PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_PACKAGES_DEBUG)) \
    )
tests_MODULES := $(sort \
        $(call get-tagged-modules,tests) \
        $(call module-installed-files, $(PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_PACKAGES_TESTS)) \
    )

# TODO: Remove the 3 places in the tree that use ALL_DEFAULT_INSTALLED_MODULES
# and get rid of it from this list.
modules_to_install := $(sort \
    $(ALL_DEFAULT_INSTALLED_MODULES) \
    $(product_FILES) \
    $(foreach tag,$(tags_to_install),$($(tag)_MODULES)) \
    $(CUSTOM_MODULES) \
  )

# Some packages may override others using LOCAL_OVERRIDES_PACKAGES.
# Filter out (do not install) any overridden packages.
overridden_packages := $(call get-package-overrides,$(modules_to_install))
ifdef overridden_packages
#  old_modules_to_install := $(modules_to_install)
  modules_to_install := \
      $(filter-out $(foreach p,$(overridden_packages),$(p) %/$(p).apk %/$(p).odex %/$(p).vdex), \
          $(modules_to_install))
endif
#$(error filtered out
#           $(filter-out $(modules_to_install),$(old_modules_to_install)))

# Don't include any GNU General Public License shared objects or static
# libraries in SDK images.  GPL executables (not static/dynamic libraries)
# are okay if they don't link against any closed source libraries (directly
# or indirectly)

# It's ok (and necessary) to build the host tools, but nothing that's
# going to be installed on the target (including static libraries).

...

# build/core/Makefile contains extra stuff that we don't want to pollute this
# top-level makefile with.  It expects that ALL_DEFAULT_INSTALLED_MODULES
# contains everything that's built during the current make, but it also further
# extends ALL_DEFAULT_INSTALLED_MODULES.
ALL_DEFAULT_INSTALLED_MODULES := $(modules_to_install)
include $(BUILD_SYSTEM)/Makefile
modules_to_install := $(sort $(ALL_DEFAULT_INSTALLED_MODULES))
ALL_DEFAULT_INSTALLED_MODULES :=


# These are additional goals that we build, in order to make sure that there
# is as little code as possible in the tree that doesn't build.
modules_to_check := $(foreach m,$(ALL_MODULES),$(ALL_MODULES.$(m).CHECKED))

# If you would like to build all goals, and not skip any intermediate
# steps, you can pass the "all" modifier goal on the commandline.
ifneq ($(filter all,$(MAKECMDGOALS)),)
modules_to_check += $(foreach m,$(ALL_MODULES),$(ALL_MODULES.$(m).BUILT))
endif

# for easier debugging
modules_to_check := $(sort $(modules_to_check))
#$(error modules_to_check $(modules_to_check))

# -------------------------------------------------------------------
# This is used to to get the ordering right, you can also use these,
# but they're considered undocumented, so don't complain if their
# behavior changes.
# An internal target that depends on all copied headers
# (see copy_headers.make).  Other targets that need the
# headers to be copied first can depend on this target.
.PHONY: all_copied_headers
all_copied_headers: ;

$(ALL_C_CPP_ETC_OBJECTS): | all_copied_headers

# All the droid stuff, in directories
.PHONY: files
files: $(modules_to_install) \
       $(INSTALLED_ANDROID_INFO_TXT_TARGET)

# -------------------------------------------------------------------

.PHONY: checkbuild
checkbuild: $(modules_to_check) droid_targets

ifeq (true,$(ANDROID_BUILD_EVERYTHING_BY_DEFAULT))
droid: checkbuild
endif

.PHONY: ramdisk
ramdisk: $(INSTALLED_RAMDISK_TARGET)

.PHONY: systemtarball
systemtarball: $(INSTALLED_SYSTEMTARBALL_TARGET)

.PHONY: boottarball
boottarball: $(INSTALLED_BOOTTARBALL_TARGET)

.PHONY: userdataimage
userdataimage: $(INSTALLED_USERDATAIMAGE_TARGET)

ifneq (,$(filter userdataimage, $(MAKECMDGOALS)))
$(call dist-for-goals, userdataimage, $(BUILT_USERDATAIMAGE_TARGET))
endif

.PHONY: userdatatarball
userdatatarball: $(INSTALLED_USERDATATARBALL_TARGET)

.PHONY: cacheimage
cacheimage: $(INSTALLED_CACHEIMAGE_TARGET)

.PHONY: bptimage
bptimage: $(INSTALLED_BPTIMAGE_TARGET)

.PHONY: vendorimage
vendorimage: $(INSTALLED_VENDORIMAGE_TARGET)

.PHONY: systemotherimage
systemotherimage: $(INSTALLED_SYSTEMOTHERIMAGE_TARGET)

.PHONY: bootimage
bootimage: $(INSTALLED_BOOTIMAGE_TARGET)

.PHONY: vbmetaimage
vbmetaimage: $(INSTALLED_VBMETAIMAGE_TARGET)

.PHONY: auxiliary
auxiliary: $(INSTALLED_AUX_TARGETS)

# Build files and then package it into the rom formats
.PHONY: droidcore
droidcore: files \
	systemimage \
	$(INSTALLED_BOOTIMAGE_TARGET) \
	$(INSTALLED_RECOVERYIMAGE_TARGET) \
	$(INSTALLED_VBMETAIMAGE_TARGET) \
	$(INSTALLED_USERDATAIMAGE_TARGET) \
	$(INSTALLED_CACHEIMAGE_TARGET) \
	$(INSTALLED_BPTIMAGE_TARGET) \
	$(INSTALLED_VENDORIMAGE_TARGET) \
	$(INSTALLED_SYSTEMOTHERIMAGE_TARGET) \
	$(INSTALLED_FILES_FILE) \
	$(INSTALLED_FILES_FILE_VENDOR) \
	$(INSTALLED_FILES_FILE_SYSTEMOTHER)

# dist_files only for putting your library into the dist directory with a full build.
.PHONY: dist_files

ifneq ($(TARGET_BUILD_APPS),)
  # If this build is just for apps, only build apps and not the full system by default.

  unbundled_build_modules :=
  ifneq ($(filter all,$(TARGET_BUILD_APPS)),)
    # If they used the magic goal "all" then build all apps in the source tree.
    unbundled_build_modules := $(foreach m,$(sort $(ALL_MODULES)),$(if $(filter APPS,$(ALL_MODULES.$(m).CLASS)),$(m)))
  else
    unbundled_build_modules := $(TARGET_BUILD_APPS)
  endif

  # Dist the installed files if they exist.
  apps_only_installed_files := $(foreach m,$(unbundled_build_modules),$(ALL_MODULES.$(m).INSTALLED))
  $(call dist-for-goals,apps_only, $(apps_only_installed_files))
  # For uninstallable modules such as static Java library, we have to dist the built file,
  # as <module_name>.<suffix>
  apps_only_dist_built_files := $(foreach m,$(unbundled_build_modules),$(if $(ALL_MODULES.$(m).INSTALLED),,\
      $(if $(ALL_MODULES.$(m).BUILT),$(ALL_MODULES.$(m).BUILT):$(m)$(suffix $(ALL_MODULES.$(m).BUILT)))\
      $(if $(ALL_MODULES.$(m).AAR),$(ALL_MODULES.$(m).AAR):$(m).aar)\
      ))
  $(call dist-for-goals,apps_only, $(apps_only_dist_built_files))

  ifeq ($(EMMA_INSTRUMENT),true)
    $(EMMA_META_ZIP) : $(apps_only_installed_files)

    $(call dist-for-goals,apps_only, $(EMMA_META_ZIP))
  endif

  $(PROGUARD_DICT_ZIP) : $(apps_only_installed_files)
  $(call dist-for-goals,apps_only, $(PROGUARD_DICT_ZIP))

  $(SYMBOLS_ZIP) : $(apps_only_installed_files)
  $(call dist-for-goals,apps_only, $(SYMBOLS_ZIP))

  $(COVERAGE_ZIP) : $(apps_only_installed_files)
  $(call dist-for-goals,apps_only, $(COVERAGE_ZIP))

.PHONY: apps_only
apps_only: $(unbundled_build_modules)

droid_targets: apps_only

# Combine the NOTICE files for a apps_only build
$(eval $(call combine-notice-files, html, \
    $(target_notice_file_txt), \
    $(target_notice_file_html_or_xml), \
    "Notices for files for apps:", \
    $(TARGET_OUT_NOTICE_FILES), \
    $(apps_only_installed_files)))


else # TARGET_BUILD_APPS
  $(call dist-for-goals, droidcore, \
    $(INTERNAL_UPDATE_PACKAGE_TARGET) \
    $(INTERNAL_OTA_PACKAGE_TARGET) \
    $(BUILT_OTATOOLS_PACKAGE) \
    $(SYMBOLS_ZIP) \
    $(COVERAGE_ZIP) \
    $(INSTALLED_FILES_FILE) \
    $(INSTALLED_FILES_FILE_VENDOR) \
    $(INSTALLED_FILES_FILE_SYSTEMOTHER) \
    $(INSTALLED_BUILD_PROP_TARGET) \
    $(BUILT_TARGET_FILES_PACKAGE) \
    $(INSTALLED_ANDROID_INFO_TXT_TARGET) \
    $(INSTALLED_RAMDISK_TARGET) \
   )

  # Put a copy of the radio/bootloader files in the dist dir.
  $(foreach f,$(INSTALLED_RADIOIMAGE_TARGET), \
    $(call dist-for-goals, droidcore, $(f)))

  ifneq ($(ANDROID_BUILD_EMBEDDED),true)
  ifneq ($(TARGET_BUILD_PDK),true)
    $(call dist-for-goals, droidcore, \
      $(APPS_ZIP) \
      $(INTERNAL_EMULATOR_PACKAGE_TARGET) \
      $(PACKAGE_STATS_FILE) \
    )
  endif
  endif

  ifeq ($(EMMA_INSTRUMENT),true)
    $(EMMA_META_ZIP) : $(INSTALLED_SYSTEMIMAGE)

    $(call dist-for-goals, dist_files, $(EMMA_META_ZIP))
  endif

# Building a full system-- the default is to build droidcore
droid_targets: droidcore dist_files

endif # TARGET_BUILD_APPS

.PHONY: docs
docs: $(ALL_DOCS)

.PHONY: sdk
ALL_SDK_TARGETS := $(INTERNAL_SDK_TARGET)
sdk: $(ALL_SDK_TARGETS)
$(call dist-for-goals,sdk win_sdk, \
    $(ALL_SDK_TARGETS) \
    $(SYMBOLS_ZIP) \
    $(COVERAGE_ZIP) \
    $(INSTALLED_BUILD_PROP_TARGET) \
)

# umbrella targets to assit engineers in verifying builds
.PHONY: java native target host java-host java-target native-host native-target \
        java-host-tests java-target-tests native-host-tests native-target-tests \
        java-tests native-tests host-tests target-tests tests java-dex
# some synonyms
.PHONY: host-java target-java host-native target-native \
        target-java-tests target-native-tests
host-java : java-host
target-java : java-target
host-native : native-host
target-native : native-target
target-java-tests : java-target-tests
target-native-tests : native-target-tests
tests : host-tests target-tests

# Phony target to run all java compilations that use javac instead of jack.
.PHONY: javac-check

ifneq (,$(filter samplecode, $(MAKECMDGOALS)))
.PHONY: samplecode
sample_MODULES := $(sort $(call get-tagged-modules,samples))
sample_APKS_DEST_PATH := $(TARGET_COMMON_OUT_ROOT)/samples
sample_APKS_COLLECTION := \
        $(foreach module,$(sample_MODULES),$(sample_APKS_DEST_PATH)/$(notdir $(module)))
$(foreach module,$(sample_MODULES),$(eval $(call \
        copy-one-file,$(module),$(sample_APKS_DEST_PATH)/$(notdir $(module)))))
sample_ADDITIONAL_INSTALLED := \
        $(filter-out $(modules_to_install) $(modules_to_check),$(sample_MODULES))
samplecode: $(sample_APKS_COLLECTION)
	@echo "Collect sample code apks: $^"
	# remove apks that are not intended to be installed.
	rm -f $(sample_ADDITIONAL_INSTALLED)
endif  # samplecode in $(MAKECMDGOALS)

.PHONY: findbugs
findbugs: $(INTERNAL_FINDBUGS_HTML_TARGET) $(INTERNAL_FINDBUGS_XML_TARGET)

.PHONY: clean
clean:
	@rm -rf $(OUT_DIR)/*
	@echo "Entire build directory removed."

.PHONY: clobber
clobber: clean

# The rules for dataclean and installclean are defined in cleanbuild.mk.

#xxx scrape this from ALL_MODULE_NAME_TAGS
.PHONY: modules
modules:
	@echo "Available sub-modules:"
	@echo "$(call module-names-for-tag-list,$(ALL_MODULE_TAGS))" | \
	      tr -s ' ' '\n' | sort -u | $(COLUMN)

.PHONY: showcommands
showcommands:
	@echo >/dev/null

.PHONY: nothing
nothing:
	@echo Successfully read the makefiles.

.PHONY: tidy_only
tidy_only:
	@echo Successfully make tidy_only.

ndk: $(SOONG_OUT_DIR)/ndk.timestamp
.PHONY: ndk

.PHONY: all_link_types
all_link_types:

endif # KATI
{%endhighlight%}

&emsp;&emsp;在main.mk中出现最早的一条规则是`.PHONY: droid`,表明了最终目标是droid这个伪目标。不过按照Makefile语言的特性，最后执行的才是规则语句，也就是droid这个依赖的推导要等到条件语句、变量赋值语句、函数语句等执行完才会开始执行。我们可以这样理解开始推导规则之前的语句大部分都是在为之后的推导做铺垫，比如设置环境变量、判断编译环境等。

&emsp;&emsp;推理到这里，真相就渐渐的浮出水面了，后面的我就不再继续了。整个编译流程我们已经有了一个大概的认识，对于更多细节还是需要读者自己去看源代码才能了解的更加透彻，这一篇文章的目的只是，让我们知道Makefile文件的使用。由于同时存在make、kati和Blueprint、Soong两套构建工具导致，在阅读Makefile文件没有那么纯粹。不过Android团队在后续应该会渐渐去掉make、kati这套构建工具，希望不要向jack，搞到一般说不搞了。

&emsp;&emsp;如果想在多了解一些Android的构建系统的话，我这里推荐几篇文章供读者阅读

- [Android编译系统简要介绍和学习计划](http://blog.csdn.net/luoshengyang/article/details/18466779)

- [理解 Android Build 系统](https://www.ibm.com/developerworks/cn/opensource/os-cn-android-build/index.html)

- [Android编译系统参考手册](http://android.cloudchou.com/)


## *4.Reference*{:.header2-font}
[跟我一起写Makefile](http://wiki.ubuntu.org.cn/%E8%B7%9F%E6%88%91%E4%B8%80%E8%B5%B7%E5%86%99Makefile)

[GNU make](http://www.gnu.org/software/make/manual/html_node/index.html?cm_mc_uid=45784307156114982261855&cm_mc_sid_50200000=1506734444)

[make makefile cmake qmake都是什么，有什么区别？](https://www.zhihu.com/question/27455963) 

[Make 命令教程](http://www.ruanyifeng.com/blog/2015/02/make.html)

[Android编译系统简要介绍和学习计划](http://blog.csdn.net/luoshengyang/article/details/18466779)

[理解 Android Build 系统](https://www.ibm.com/developerworks/cn/opensource/os-cn-android-build/index.html)

[Android编译系统参考手册](http://android.cloudchou.com/)


[Android7.0 Ninja编译原理](http://blog.csdn.net/chaoy1116/article/details/53063082)