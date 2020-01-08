
programPath = lfs.realpath(lfs.currentdir())
package.path = programPath .. "\\?.lua;" .. package.path
package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"

function LuaExportStart()
  socket = require("socket")
  fps_log_file = nil
  fps_log = io.open(lfs.writedir().."/Logs/fps_tracklog"..socket.gettime()..".log", "w")
end


function LuaExportStop()
  if fps_log_file then
	   fps_log_file:close()
	   fps_log_file = nil
  end
  if cli then
    cli:close()
  end
end


function WriteFpsLog()
    local start_ts = socket.gettime()
    fps_log:write(start_ts.."\r\n")
end


function LuaExportAfterNextFrame()
  WriteFpsLog()
end
