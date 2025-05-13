
local LrApplication   = import( "LrApplication" )
local LrTasks         = import( "LrTasks" )
local LrExportSession = import( "LrExportSession" )

LrTasks.startAsyncTask( function()
	local activeCatalog = LrApplication.activeCatalog()
	local sourceFrames = activeCatalog.targetPhotos
	local exportSession = LrExportSession( {
		exportSettings = {
			LR_exportServiceProvider       = "com.github.gkyle.enhance",
			LR_exportServiceProviderTitle  = "Enhance AI",
			LR_format                      = "TIFF",
			LR_tiff_compressionMethod      = "compressionMethod_None",
			LR_export_bitDepth             = 16,
			LR_export_colorSpace           = "sRGB",
			LR_minimizeEmbeddedMetadata    = false,
			LR_metadata_keywordOptions     = "lightroomHierarchical",
			LR_removeLocationMetadata      = false
			},
		photosToExport = sourceFrames,
		} )
	exportSession:doExportOnCurrentTask()
end )
