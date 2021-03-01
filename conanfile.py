from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


class VkBootstrapConan(ConanFile):
    name = "vk-bootstrap"
    description = "Vulkan bootstraping library."
    license = "MIT"
    topics = ("conan", "vk-bootstrap", "vulkan")
    homepage = "https://github.com/charles-lunarg/vk-bootstrap"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    exports_sources =  ["CMakeLists.txt", "patches/**"]
    generators = "cmake"
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, 11)
        if self.settings.compiler == "Visual Studio" and self.options.shared:
            raise ConanInvalidConfiguration("vk-boostrap shared not supported with Visual Studio")

    def requirements(self):
        self.requires("vulkan-headers/1.2.170.0")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def _patch_sources(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmakelists = os.path.join(self._source_subfolder, "CMakeLists.txt")
        # We don't need full Vulkan SDK, just headers, but vulkan-headers recipe alone can't emulate FindVulkan.cmake
        tools.replace_in_file(cmakelists, "find_package(Vulkan REQUIRED)", "")
        # No warnings as errors
        tools.replace_in_file(cmakelists, "-pedantic-errors", "")
        tools.replace_in_file(cmakelists, "/WX", "")

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["VK_BOOTSTRAP_TEST"] = False
        self._cmake.configure()
        return self._cmake

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE.txt", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["vk-bootstrap"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
