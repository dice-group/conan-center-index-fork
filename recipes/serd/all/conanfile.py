import os

from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import rmdir

required_conan_version = ">=1.33.0"


class Recipe(ConanFile):
    name = "serd"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://drobilla.net/software/serd.html"
    description = "A lightweight C library for RDF syntax"
    topics = "linked-data", "semantic-web", "rdf", "turtle", "trig", "ntriples", "nquads"
    settings = "build_type", "compiler", "os", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    license = "ISC"
    exports_sources = "src*", "include*", "doc*", "waf", "wscript", "waflib*", "serd.pc.in"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version]["serd"],
                  destination=self.folders.base_source,
                  strip_root=True)
        # serd comes with its own modification of the waf build system
        # It seems to be used only by serd and will be replaced in future versions with meson.
        # So it makes no sense to create a separate conan package for the build system.
        from pathlib import Path
        tools.get(**self.conan_data["sources"][self.version]["autowaf"],
                  destination=Path(self.folders.base_source).joinpath("waflib"),
                  strip_root=True)

    def configure(self):
        # its a C library. So C++ properties compiler.{libcxx,cppstd} are not required.
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Don't know how to setup WAF for VS.")

    def build(self):
        args = ["--no-utils", " --prefix={}".format(self.folders.package_folder)]
        if not self.options["shared"]:
            args += ["--static", "--no-shared"]
        if self.options["fPIC"]:
            args += ["-fPIC"]
        args = " ".join(arg for arg in args)

        cflags = []
        if self.settings.build_type in ["Debug", "RelWithDebInfo"]:
            cflags += ["-g"]
        if self.settings.build_type in ["Release", "RelWithDebInfo"]:
            cflags += ["-O3"]
        if self.settings.build_type in ["Release", "MinSizeRel"]:
            cflags += ["-DNDEBUG"]
        if self.settings.build_type == "MinSizeRel":
            cflags += ["-Os"]
        cflags = " ".join(cflag for cflag in cflags)

        self.run(f'CFLAGS="{cflags}" ./waf configure {args}')
        self.run('./waf build')

    def package(self):
        self.run('./waf install')
        rmdir(os.path.join(self.package_folder, "share"))
        rmdir(os.path.join(self.package_folder, "lib/pkgconfig"))
        self.copy("COPYING", src=self.folders.base_export_sources, dst="licenses")

    def package_info(self):
        libname = "{}-0".format(self.name)
        self.cpp_info.libs = [libname]
        self.cpp_info.includedirs = [f"include/{libname}/"]
