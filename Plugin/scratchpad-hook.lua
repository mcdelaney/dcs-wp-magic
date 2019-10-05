require "os"

function scratchpad_load()
    programPath = lfs.realpath(lfs.currentdir())
    package.path = programPath .. "\\?.lua;" .. package.path
    package.path = package.path .. ";.\\Scripts\\?.lua;.\\Scripts\\UI\\?.lua;"

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

    local scratchpad = {
        logFile = io.open(lfs.writedir() .. [[Logs\Scratchpad.log]], "w")
    }

    local dirPath = lfs.writedir() .. [[Scratchpad\]]

    local function loadCoords()
        current_page = 'coords'
        scratchpad.log("loading page coordinates...")
        textarea:setText(coord_data)
        -- targetarea:setText(target_data)
        window:setText("Coords")
    end

    local function loadTargets()
        current_page = "targets"
        scratchpad.log("loading page targets...")
        textarea:setText(target_data)
        -- targetarea:setText(target_data)
        window:setText("Targets")
    end

    function scratchpad.loadConfiguration()
        scratchpad.log("Loading config file...")
        local tbl = Tools.safeDoFile(lfs.writedir() .. "Config/ScratchpadConfig.lua", false)
        if (tbl and tbl.config) then
            scratchpad.log("Configuration exists...")
            scratchpad.config = tbl.config
            -- config migration
            -- add default fontSize config
            if scratchpad.config.fontSize == nil then
                scratchpad.config.fontSize = 16
                scratchpad.saveConfiguration()
            end
            -- move content into text file
            if scratchpad.config.content ~= nil then
                scratchpad.config.content = nil
                scratchpad.saveConfiguration()
            end
        else
            scratchpad.log("Configuration not found, creating defaults...")
            scratchpad.config = {
                hotkey = "Ctrl+Shift+x",
                windowPosition = {x = 200, y = 200},
                windowSize = {w = 350, h = 150},
                fontSize = 14
            }
            scratchpad.saveConfiguration()
        end
    end

    function scratchpad.saveConfiguration()
        U.saveInFile(scratchpad.config, "config", lfs.writedir() .. "Config/ScratchpadConfig.lua")
    end

    function scratchpad.log(str)
        if not str then
            return
        end
        if scratchpad.logFile then
            scratchpad.logFile:write("[" .. os.date("%H:%M:%S") .. "] " .. str .. "\r\n")
            scratchpad.logFile:flush()
        end
    end

    local function updateCoordinates()
        local resp, status, err = http.request("http://127.0.0.1:5000/coords/" .. fmt .. "/" .. status)
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
        scratchpad.log(status)
        scratchpad.log("Requesting coordinate entry...")
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

    function scratchpad.createWindow()
        local file_path = lfs.writedir() .. [[Scratchpad\]] .. [[target.txt]]
        local file, err = io.open(file_path, "w")
        file:write("")
        file:close()

        window = DialogLoader.spawnDialogFromFile(lfs.writedir() .. "Scripts\\Scratchpad\\ScratchpadWindow.dlg", cdata)
        windowDefaultSkin = window:getSkin()
        panel = window.Box
        textarea = panel.ScratchpadEditBox
        -- targetarea = panel.ScratchpadTargetBox
        coordButton = panel.ScratchpadCoordButton
        coordButton:setState(true)

        targetButton = panel.ScratchpadTargetButton
        enterCoordsBtn = panel.ScratchpadEnterCoordsButton
        sendCoordsBtn = panel.ScratchpadSendCoordsButton
        clearCoordsBtn = panel.ScratchpadClearCoordsButton
        stopCoordsBtn = panel.ScratchpadStopCoordsButton
        preciseCoordsBtn = panel.ScratchpadPreciseCoordsButton
        keepAllBtn = panel.ScratchpadKeepAllButton
        -- singleRackBtn = panel.ScratchpadSingleRackButton
        -- doubleRackBtn = panel.ScratchpadDoubleRackButton
        -- doubleRackBtn:setState(true)

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
        skin.skinData.states.released[1].text.fontSize = scratchpad.config.fontSize
        textarea:setSkin(skin)
        -- targetarea:setSkin(skin)

        scratchpad.log("Configuring callbacks...")
        coordButton:addMouseDownCallback(
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

        keepAllBtn:addMouseDownCallback(
            function(self)
                if status == "alive" then
                    status = "all"
                else
                    status = "alive"
                end
            end
        )

        scratchpad.log("Adding section callbacks...")
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

        scratchpad.log("Adding section callbacks...")
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
            scratchpad.config.windowPosition.x,
            scratchpad.config.windowPosition.y,
            scratchpad.config.windowSize.w,
            scratchpad.config.windowSize.h
        )
        scratchpad.handleResize(window)

        window:addHotKeyCallback(
            scratchpad.config.hotkey,
            function()
                if isHidden == true then
                    scratchpad.show()
                else
                    scratchpad.hide()
                end
            end
        )
        window:addSizeCallback(scratchpad.handleResize)
        window:addPositionCallback(scratchpad.handleMove)

        window:setVisible(true)
        loadCoords()

        scratchpad.hide()
        scratchpad.log("Scratchpad Window created")
    end

    function scratchpad.setVisible(b)
        window:setVisible(b)
    end

    function scratchpad.handleResize(self)
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

        local offset = offset+50+20
        keepAllBtn:setBounds(offset, h - 120, 50, 20)

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

        scratchpad.config.windowSize = {w = w, h = h}
        scratchpad.saveConfiguration()
    end

    function scratchpad.handleMove(self)
        local x, y = self:getPosition()
        scratchpad.config.windowPosition = {x = x, y = y}
        scratchpad.saveConfiguration()
    end

    function scratchpad.show()
        if window == nil then
            local status, err = pcall(scratchpad.createWindow)
          end
            if not status then
                net.log("[Scratchpad] Error creating window: " .. tostring(err))
        end

        window:setVisible(true)
        window:setSkin(windowDefaultSkin)
        panel:setVisible(true)
        window:setHasCursor(true)
        enterCoordsBtn:setVisible(true)
        coordButton:setVisible(true)
        targetButton:setVisible(true)

        isHidden = false
    end

    function scratchpad.hide()
        window:setSkin(windowSkinHidden)
        panel:setVisible(false)
        textarea:setFocused(false)
        -- targetarea:setFocused(false)
        window:setHasCursor(false)
        -- window.setVisible(false) -- if you make the window invisible, its destroyed
        -- unlockKeyboardInput(true)
        -- window = nil
        isHidden = true
    end

    function scratchpad.onSimulationFrame()
        if scratchpad.config == nil then
            scratchpad.loadConfiguration()
        end

        if not window then
            scratchpad.log("Creating Scratchpad window hidden...")
            scratchpad.createWindow()
            scratchpad.log("Window created successfully...")
        end
    end

    DCS.setUserCallbacks(scratchpad)

    net.log("[Scratchpad] Loaded ...")
end

local status, err = pcall(scratchpad_load)
if not status then
    net.log("[Scratchpad] Load Error: " .. tostring(err))
end
