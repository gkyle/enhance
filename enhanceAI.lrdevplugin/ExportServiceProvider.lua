local LrApplication = import("LrApplication")
local LrErrors      = import("LrErrors")
local LrFileUtils   = import("LrFileUtils")
local LrPathUtils   = import("LrPathUtils")
local LrDate        = import("LrDate")
local LrShell       = import("LrShell")
local LrTasks       = import("LrTasks")
local LrLogger      = import("LrLogger")
local myLogger      = LrLogger("enhanceai")

myLogger:enable("logfile")

require("Util")

-- metadata fields to copy from exported source to imported copy
METADATA_FIELDS = {
	"rating",
	"dateCreated",
}

-- When app returns, copy resulting files to catalog
function onFinish(status, tempPath, sourcePhoto, inputFiles)
	myLogger:trace("Finished. Syncing files back to LRC.")
	local catalog = LrApplication.activeCatalog()

	for filename in LrFileUtils.files(tempPath) do
		myLogger:trace(string.format("filename: %s", filename))
        if not inputFiles[filename] then
			srcPath = sourcePhoto:getRawMetadata("path")
			local copyPath = LrPathUtils.child(LrPathUtils.parent(srcPath), LrPathUtils.leafName(filename))
			myLogger:trace(string.format("Copy to LRC: srcPath: %s", filename))
			myLogger:trace(string.format("Copy to LRC: dstPath: %s", copyPath))
			catalog:withWriteAccessDo("Copying file", function(context)
				success, message = LrFileUtils.copy(filename, copyPath)
				if success then
					local photo = catalog:addPhoto(copyPath, sourcePhoto, "above")
					for i, field in ipairs(METADATA_FIELDS) do
						local value = sourcePhoto:getFormattedMetadata(field)
						if value ~= nil then
							myLogger:trace(string.format("Setting %s to %s", field, value))
							photo:setRawMetadata(field, value)
						end
					end
				else
					myLogger:trace("Unable to copy file ")
					myLogger:trace(message)
				end				
			end)
        end
	end
end

processRenderedPhotos = function(functionContext, exportContext)
	-- Get path to Enhance AI app
	success, appPath = Util.findPath()
	if not success then
		return
	end

	-- Use a temporary directory to pass files in/out of Enhance AI
	local tempPath = Util.makeTempDir()
	local exportSession = exportContext.exportSession
	local catalog = LrApplication.activeCatalog()
	local sourcePhoto = catalog:getTargetPhoto()

	-- We export the first file in selection
	if exportSession:countRenditions() > 0 then
		local progressScope
		progressScope = exportContext:configureProgress({
			title = LOC(string.format("$$$/Enhance AI/Upload/Progress=Exporting 1 photo to Enhance AI", 1))
		})

		-- export
		local i, rendition = exportContext:renditions({ stopIfCanceled = true })(0)
		local success, pathOrMessage = rendition:waitForRender()
		sourcePath = rendition.photo:getRawMetadata('masterPhoto'):getRawMetadata('path')
		if progressScope:isCanceled() then
			LrFileUtils.delete(tempPath)
			return
		end

		if not success then
			myLogger:trace("Unable to export: "..pathOrMessage)
			LrErrors.throwUserError("Unable to export: "..pathOrMessage)
			LrFileUtils.delete(tempPath)
			return
		end

		-- copy
		local basename = LrPathUtils.leafName(rendition.destinationPath)
		local copyPath = LrPathUtils.child(tempPath, basename)
		local success = Util.copyFile(rendition.destinationPath, copyPath)
		if not success then
			LrFileUtils.delete(tempPath)
			return
		end
	end

	-- For Windows, show the command window
	local command = '"start /wait cmd.exe /c '..appPath..' '..tempPath..'"'
	inputFiles = {}
	for filename in LrFileUtils.files(tempPath) do
		inputFiles[filename] = true
	end

	local sourceDir = LrPathUtils.parent(sourcePath)

	LrTasks.startAsyncTask(function ()
		local ret = LrTasks.execute(command)
		onFinish(ret, tempPath, sourcePhoto, inputFiles)
	end)
end


return {
	showSections = { 'fileNaming', 'fileSettings', 'imageSettings', 'metadata' },
	allowFileFormats = { 'TIFF', 'JPEG' },
	allowColorSpaces = { 'sRGB' },
	hidePrintResolution = false,
	exportPresetFields = { key = 'path', default = '' },
	processRenderedPhotos = processRenderedPhotos,
}
