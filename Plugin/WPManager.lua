-- WPManagerrequire "os"
programPath = lfs.realpath(lfs.currentdir())
package.path = programPath .. "\\?.lua;" .. package.path
package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"

local io = require("io")


function wpmanager_load()
    local io = require("io")
    -- local http = require("socket.http")
    require("LuaSocket.socket")
    require("LuaSocket.url")
    require("LuaSocket.http")
    local http = require('socket.http')

    local lfs = require("lfs")
    local U = require("me_utilities")
    local Skin = require("Skin")
    local DialogLoader = require("DialogLoader")
    local Tools = require("tools")
    local Input = require("Input")

    local isHidden = true
    -- local keyboardLocked = false
    local window = nil
    local windowDefaultSkin = nil
    local windowSkinHidden = Skin.windowSkinChatMin()
    local panel = nil
    local textarea = nil
    local section_val = nil
    local target_val = nil
    local coord_data = ""
    local target_data = ""
    local coord_request = ""
    local sections = {}
    local targets = {}
    local current_page = 'coords'
    local status = 'alive'
    local fmt = "dms"

    local wpmanager = {
        logFile = io.open(lfs.writedir() .. [[Logs\WP-Manager.log]], "w")
    }

    local dirPath = lfs.writedir() .. [[WP-Manager\]]

    local function loadCoords()
        current_page = 'coords'
        wpmanager.log("loading page coordinates...")
        textarea:setText(coord_data)
        window:setText("Coords")
    end

    local function loadTargets()
        current_page = "targets"
        wpmanager.log("loading page targets...")
        textarea:setText(target_data)
        window:setText("Targets")
    end

    function wpmanager.loadConfiguration()
        wpmanager.log("Loading config file...")
        local tbl = Tools.safeDoFile(lfs.writedir() .. "Config/WP-Manager-config.lua", false)
        if (tbl and tbl.config) then
            wpmanager.log("Configuration exists...")
            wpmanager.config = tbl.config
            if wpmanager.config.fontSize == nil then
                wpmanager.config.fontSize = 14
                wpmanager.saveConfiguration()
            end
            -- move content into text file
            if wpmanager.config.content ~= nil then
                wpmanager.config.content = nil
                wpmanager.saveConfiguration()
            end
        else
            wpmanager.log("Configuration not found, creating defaults...")
            wpmanager.config = {
                hotkey = "Ctrl+Shift+x",
                windowPosition = {x = 200, y = 200},
                windowSize = {w = 400, h = 150},
                fontSize = 14
            }
            wpmanager.saveConfiguration()
        end
    end

    function wpmanager.saveConfiguration()
        U.saveInFile(wpmanager.config, "config", lfs.writedir() .. "Config/WP-Manager-config.lua")
    end

    function wpmanager.log(str)
        if not str then
            return
        end
        if wpmanager.logFile then
            wpmanager.logFile:write("[" .. os.date("%H:%M:%S") .. "] " .. str .. "\r\n")
            wpmanager.logFile:flush()
        end
    end

    local function updateCoordinates()

        local resp, status, err = http.request("http://127.0.0.1:5000/coords/" .. fmt)
        if status ~= 200 then
            return "Error updating coordinates!"
        end
        coord_data = resp
    end

    local function enterCoordinates()
        coord_request = coord_request .. section_val .. "," .. target_val .. "|"
        target_data = target_data .. section_val .. "," .. target_val .. "\n"
        if current_page == 'targets' then
          textarea:setText(target_data)
        end
    end

    local function sendCoordinates()
        local rack = "2"
        local resp, status, err = http.request("http://127.0.0.1:5000/enter_coords/" .. rack .. "/" .. coord_request)
        wpmanager.log(status)
        wpmanager.log("Requesting coordinate entry...")
        if status == 200 then
          target_data = ""
          coord_data = ""
        else
          textarea:setText("Error entering coordinates!")
        end
    end

    local function stopCoordinates()
        local resp = http.request("http://127.0.0.1:5000/stop")
    end

    local function clearCoordinates()
      -- Unselect any section or target boxes that are pressed
      for key, val in pairs(sections) do
          sections[key]:setState(false)
      end
      for key, val in pairs(targets) do
          targets[key]:setState(false)
      end
      target_val = nil
      section_val = nil
      target_data = ""
      coord_request = ""
      if current_page == "targets" then
        loadTargets()
      end
    end

    function wpmanager.createWindow()
        window = DialogLoader.spawnDialogFromFile(lfs.writedir() .. "Scripts\\WP-Manager\\WPManager.dlg")
        -- , cdata)
        windowDefaultSkin = window:getSkin()
        panel = window.Box
        textarea = panel.WPManagerEditBox
        coordButton = panel.WPManagerCoordButton
        coordButton:setState(true)

        targetButton = panel.WPManagerTargetButton
        enterCoordsBtn = panel.WPManagerEnterCoordsButton
        sendCoordsBtn = panel.WPManagerSendCoordsButton
        clearCoordsBtn = panel.WPManagerClearCoordsButton
        stopCoordsBtn = panel.WPManagerStopCoordsButton
        preciseCoordsBtn = panel.WPManagerPreciseCoordsButton
        -- keepAllBtn = panel.WPManagerKeepAllButton

        table.insert(sections, panel.CoordSection1)
        table.insert(sections, panel.CoordSection2)
        table.insert(sections, panel.CoordSection3)
        table.insert(sections, panel.CoordSection4)
        table.insert(sections, panel.CoordSection5)
        table.insert(sections, panel.CoordSection6)
        table.insert(sections, panel.CoordSection7)
        table.insert(sections, panel.CoordSection8)
        table.insert(sections, panel.CoordSection9)
        table.insert(sections, panel.CoordSection10)
        table.insert(sections, panel.CoordSection11)
        table.insert(sections, panel.CoordSection12)
        table.insert(sections, panel.CoordSection13)
        table.insert(sections, panel.CoordSection14)
        table.insert(sections, panel.CoordSection15)

        table.insert(targets, panel.CoordTarget1)
        table.insert(targets, panel.CoordTarget2)
        table.insert(targets, panel.CoordTarget3)
        table.insert(targets, panel.CoordTarget4)
        table.insert(targets, panel.CoordTarget5)
        table.insert(targets, panel.CoordTarget6)
        table.insert(targets, panel.CoordTarget7)
        table.insert(targets, panel.CoordTarget8)
        table.insert(targets, panel.CoordTarget9)
        table.insert(targets, panel.CoordTarget10)
        table.insert(targets, panel.CoordTarget11)
        table.insert(targets, panel.CoordTarget12)
        table.insert(targets, panel.CoordTarget13)
        table.insert(targets, panel.CoordTarget14)
        table.insert(targets, panel.CoordTarget15)

        -- setup textarea
        local skin = textarea:getSkin()
        skin.skinData.states.released[1].text.fontSize = wpmanager.config.fontSize
        textarea:setSkin(skin)

        wpmanager.log("Configuring callbacks...")
        coordButton:addMouseDownCallback(
            function(self)
                updateCoordinates()
                loadCoords()
                targetButton:setState(false)
            end
        )

        window:addHotKeyCallback(
            "Ctrl+Shift+y",
            function(self)
                updateCoordinates()
                loadCoords()
                targetButton:setState(false)
            end
        )

        targetButton:addMouseDownCallback(
            function(self)
                loadTargets()
                coordButton:setState(false)
            end
        )

        enterCoordsBtn:addMouseDownCallback(
            function(self)
                local result = enterCoordinates()
            end
        )

        sendCoordsBtn:addMouseDownCallback(
            function(self)
                sendCoordinates()
                clearCoordinates()
            end
        )

        clearCoordsBtn:addMouseDownCallback(
            function(self)
                clearCoordinates()
            end
        )

        stopCoordsBtn:addMouseDownCallback(
            function(self)
                stopCoordinates()
                clearCoordinates()
            end
        )
        preciseCoordsBtn:addMouseDownCallback(
            function(self)
                if fmt == "dms" then
                    fmt = "precise"
                else
                    fmt = "dms"
                end
            end
        )

        wpmanager.log("Adding section callbacks...")
        for k, v in pairs(sections) do
            sections[k]:addMouseDownCallback(
                function(self)
                    section_val = tostring(k)
                    if not (target_val == nil) then
                        enterCoordsBtn:setEnabled(true)
                    end
                    for key, val in pairs(sections) do
                        if not (key == k) then
                            sections[key]:setState(false)
                        end
                    end
                end
            )
        end

        wpmanager.log("Adding section callbacks...")
        for k, v in pairs(targets) do
            targets[k]:addMouseDownCallback(
                function(self)
                    target_val = tostring(k)
                    if not (section_val == nil) then
                        enterCoordsBtn:setEnabled(true)
                    end
                    for key, val in pairs(targets) do
                        if not (key == k) then
                            targets[key]:setState(false)
                        end
                    end
                end
            )
        end

        -- setup window
        window:setBounds(
            wpmanager.config.windowPosition.x,
            wpmanager.config.windowPosition.y,
            wpmanager.config.windowSize.w,
            wpmanager.config.windowSize.h
        )
        wpmanager.handleResize(window)

        window:addHotKeyCallback(
            wpmanager.config.hotkey,
            function()
                if isHidden == true then
                    wpmanager.show()
                else
                    wpmanager.hide()
                end
            end
        )


        window:addSizeCallback(wpmanager.handleResize)
        window:addPositionCallback(wpmanager.handleMove)

        window:setVisible(true)
        loadCoords()

        wpmanager.hide()
        wpmanager.log("WPManager Window created")

        local dev = GetSelf()
        m=getmetatable(dev)
        str=dump("GetSelf meta",m)
        local lines=strsplit("\n",str)
        for k,v in ipairs(lines) do
           wpmanager.log(v)
        end


    end

    function wpmanager.setVisible(b)
        window:setVisible(b)
    end

    function wpmanager.handleResize(self)
        local w, h = self:getSize()
        panel:setBounds(0, 0, w, h - 20)
        textarea:setBounds(0, 0, w, h - 20 - 20 - 20 - 20 - 40)
        offset = 0
        coordButton:setBounds(offset, h - 120, 60, 20)
        local offset = offset+60+20
        targetButton:setBounds(offset, h - 120, 60, 20)
        local offset = offset+50+20
        enterCoordsBtn:setBounds(offset, h - 120, 50, 20)
        local offset = offset+50+20
        sendCoordsBtn:setBounds(offset, h - 120, 50, 20)
        local offset = offset+50+20
        clearCoordsBtn:setBounds(offset, h - 120, 50, 20)
        local offset = offset+50+20
        stopCoordsBtn:setBounds(offset, h - 120, 50, 20)
        local offset = offset+50+20
        preciseCoordsBtn:setBounds(offset, h - 120, 50, 20)

        -- local offset = offset+50+20
        -- keepAllBtn:setBounds(offset, h - 120, 50, 20)

        local w = -40
        for k, v in pairs(sections) do
            w = w + 40
            sections[k]:setBounds(w, h - 100, 40, 20)
        end

        local w = -40
        for k, v in pairs(targets) do
            w = w + 40
            targets[k]:setBounds(w, h - 80, 40, 20)
        end

        wpmanager.config.windowSize = {w = w, h = h}
        wpmanager.saveConfiguration()
    end

    function wpmanager.handleMove(self)
        local x, y = self:getPosition()
        wpmanager.config.windowPosition = {x = x, y = y}
        wpmanager.saveConfiguration()
    end

    function wpmanager.show()
        if window == nil then
            local status, err = pcall(wpmanager.createWindow)
          end
            if not status then
                wpmanager.log("[WP-Manager] Error creating window: " .. tostring(err))
        end

        window:setVisible(true)
        window:setSkin(windowDefaultSkin)
        panel:setVisible(true)
        window:setHasCursor(true)
        enterCoordsBtn:setVisible(true)
        coordButton:setVisible(true)
        targetButton:setVisible(true)
        -- textarea:setFocused(false)
        -- unlockKeyboardInput(false)
        isHidden = false
    end

    function wpmanager.hide()
        window:setSkin(windowSkinHidden)
        panel:setVisible(false)
        textarea:setFocused(false)
        -- targetarea:setFocused(false)
        window:setHasCursor(false)
        -- unlockKeyboardInput(false)
        -- window = nil
        isHidden = true
    end

    function wpmanager.onSimulationFrame()
        if wpmanager.config == nil then
            wpmanager.loadConfiguration()
        end

        if not window then
            wpmanager.log("Creating WP-Manager window hidden...")
            wpmanager.createWindow()
            wpmanager.log("Window created successfully...")
        end
    end

    DCS.setUserCallbacks(wpmanager)

    wpmanager.log("[WP-Manager] Loaded ...")
end


local status, err = pcall(wpmanager_load)
if not status then
    local logFile = io.open(lfs.writedir() .. [[Logs\WP-Manager_Error.log]], "w")
    logFile.write("[WP-Manager] Load Error: " .. tostring(err))
    logFile:flush()
end



function LuaExportStart()
  socket = require("socket")
  cli = socket.tcp()
  cli:connect("127.0.0.1", 5000)
end


function LuaExportStop()
  cli:close()
end


function LuaExportAfterNextFrame()
  username = LoGetPilotName()
  if username == nil then
    username = "someone_somewhere"
  end
  cli:send("GET /set_username/" .. username .. " HTTP/1.1\r\nHost: 127.0.0.1:5000\r\n\r\n")
end
