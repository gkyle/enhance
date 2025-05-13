return {
    VERSION = { major=0, minor=1, revision=4, },
  
    LrSdkVersion = 14.2,
    LrSdkMinimumVersion = 4.0,
  
    LrToolkitIdentifier = "com.github.gkyle.enhance",
    LrPluginName = "Enhance AI",
    LrPluginInfoUrl="https://www.github.com/gkyle/enhance",

	LrExportMenuItems = {
        title = "Enhance with Enhance AI",  -- in File > Plug-in Extras
        file = "Export.lua",
		enabledWhen = "photosSelected",
	},

	LrExportServiceProvider = {
        title = "Enhance AI",
        file = "ExportServiceProvider.lua",
		builtInPresetsDir = "presets",
	},
  }