local LrDate        = import("LrDate")
local LrErrors      = import("LrErrors")
local LrFileUtils   = import("LrFileUtils")
local LrPathUtils   = import("LrPathUtils")
local LrLogger      = import("LrLogger")
local myLogger      = LrLogger("enhanceai2")

myLogger:enable("logfile")

Util = {}

-- find path from a text file output each time the app runs
Util.findPath = function()
    pathPath = LrPathUtils.standardizePath(_PLUGIN.path.."/PluginPath.txt")
    myLogger:trace(string.format("Util.processRenderedPhotos pathPath: %s", pathPath))
    if LrFileUtils.exists(pathPath) then
        appPath = LrFileUtils.readFile(pathPath)
        if LrFileUtils.exists(appPath) then
            return true, appPath
        else
            errmsg = "Could not find path to application: "..appPath.."."
        end
    else
        errmsg = "Could not find path to application. Try running Enhance AI directly, then try again."
    end
    myLogger:trace(errmsg)
    LrErrors.throwUserError(errmsg)
    return false, nil
end

Util.makeTempDir = function()
	local parentTempPath = LrPathUtils.getStandardFilePath("temp")
	local tempPath = nil
	repeat
	do
		local now = LrDate.currentTime()
		tempPath = LrPathUtils.child(parentTempPath, "Lightroom_Export_"..LrDate.timeToUserFormat(now, "%Y%m%d%H%M%S"))
		if LrFileUtils.exists(tempPath) then
			tempPath = nil
		else
			LrFileUtils.createAllDirectories(tempPath)
		end
	end until tempPath
	myLogger:trace(string.format("tempPath: %s", tempPath))

    return tempPath
end

Util.copyFile = function(srcPath, destPath)
    local success, message

    myLogger:trace(string.format("srcPath: %s", srcPath))
    myLogger:trace(string.format("dstPath: %s", destPath))
    success, message = LrFileUtils.copy(srcPath, destPath)

    if success then
        return true
    end

    if message == nil then
        message = " (reason unknown)"
    end
    myLogger:trace("Unable to copy file "..srcPath..message)
    LrErrors.throwUserError("Unable to copy: "..srcPath..message)

    return false
end