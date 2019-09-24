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
    local keyboardLocked = false
    local window = nil
    local windowDefaultSkin = nil
    local windowSkinHidden = Skin.windowSkinChatMin()
    local panel = nil
    local textarea = nil
    local section_val = nil
    local target_val = nil
    local coord_request = ""
    local sections = {}
    local targets = {}

    local scratchpad = {
        logFile = io.open(lfs.writedir() .. [[Logs\Scratchpad.log]], "w")
    }

    local dirPath = lfs.writedir() .. [[Scratchpad\]]
    local currentPage = nil
    local pagesCount = 0
    local pages = {}

    local function loadPage(page)
        scratchpad.log("loading page " .. page.path)
        file, err = io.open(page.path, "r")
        if err then
            scratchpad.log("Error reading file: " .. page.path)
            return ""
        else
            local content = file:read("*all")
            file:close()
            textarea:setText(content)
            -- update title
            window:setText(page.name)
        end
    end

    local function nextPage()
        if pagesCount == 0 then
            return
        end

        local lastPage = nil
        for _, page in pairs(pages) do
            if currentPage == nil or (lastPage ~= nil and lastPage.path == currentPage) then
                loadPage(page)
                currentPage = page.path
                return
            end
            lastPage = page
        end

        -- restart at the beginning
        loadPage(pages[1])
        currentPage = pages[1].path
    end

    local function prevPage()
        local lastPage = nil
        for i, page in pairs(pages) do
            if currentPage == nil or (page.path == currentPage and i ~= 1) then
                loadPage(lastPage)
                currentPage = lastPage.path
                return
            end
            lastPage = page
        end
        -- restart at the end
        loadPage(pages[pagesCount])
        currentPage = pages[pagesCount].path
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

        -- scan scratchpad dir for pages
        for name in lfs.dir(dirPath) do
            local path = dirPath .. name
            scratchpad.log(path)
            if lfs.attributes(path, "mode") == "file" then
                if name:sub(-4) ~= ".txt" then
                    scratchpad.log("Ignoring file " .. name .. ", because of it doesn't seem to be a text file (.txt)")
                elseif lfs.attributes(path, "size") > 1024 * 1024 then
                    scratchpad.log("Ignoring file " .. name .. ", because of its file size of more than 1MB")
                else
                    scratchpad.log("found page " .. path)
                    table.insert(
                        pages,
                        {
                            name = name:sub(1, -5),
                            path = path
                        }
                    )
                    pagesCount = pagesCount + 1
                end
            end
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

    local function unlockKeyboardInput(releaseKeyboardKeys)
        if keyboardLocked then
            DCS.unlockKeyboardInput(releaseKeyboardKeys)
            keyboardLocked = false
        end
    end

    local function lockKeyboardInput()
        if keyboardLocked then
            return
        end

        local keyboardEvents = Input.getDeviceKeys(Input.getKeyboardDeviceName())
        DCS.lockKeyboardInput(keyboardEvents)
        keyboardLocked = true
    end

    local function updateCoordinates()
        local resp, status, err = http.request("http://127.0.0.1:5000/coords/dms")
        scratchpad.log(resp)
        if status ~= 200 then
            return "Error updating coordinates!"
        end
        file_path = lfs.writedir() .. [[Scratchpad\]] .. [[coords.txt]]
        file, err = io.open(file_path, "r")
        if err then
            scratchpad.log("Error reading file: " .. file_path)
            file:close()
            return ""
        else
            local content = file:read("*all")
            file:close()
            scratchpad.log("Data collected")
            return content
        end
    end

    local function enterCoordinates()
        coord_request = coord_request .. section_val .. "," .. target_val .. "|"
        file_path = lfs.writedir() .. [[Scratchpad\]] .. [[target.txt]]
        file, err = io.open(file_path, "a")
        file:write(section_val .. "," .. target_val .. "\n")
        file:close()
    end

    local function sendCoordinates()
        local resp, status, err = http.request("http://127.0.0.1:5000/enter_coords/" .. coord_request)
        scratchpad.log(status)
        scratchpad.log("Requesting coordinate entry...")
        if status == 200 then
        else
          textarea:setText("Error entering coordinates!")
        end
    end

    local function stopCoordinates()
        local resp = http.request("http://127.0.0.1:5000/stop")
    end

    local function clearCoordinates()
      local file_path = lfs.writedir() .. [[Scratchpad\]] .. [[target.txt]]
      local file, err = io.open(file_path, "w")
      file:write("")
      file:close()
      -- Unselect any section or target boxes that are pressed
      for key, val in pairs(sections) do
          sections[key]:setState(false)
      end
      for key, val in pairs(targets) do
          targets[key]:setState(false)
      end
      target_val = nil
      section_val = nil
      coord_request = ""
    end

    function scratchpad.createWindow()
        local file_path = lfs.writedir() .. [[Scratchpad\]] .. [[target.txt]]
        local file, err = io.open(file_path, "w")
        file:close()

        window = DialogLoader.spawnDialogFromFile(lfs.writedir() .. "Scripts\\Scratchpad\\ScratchpadWindow.dlg", cdata)
        windowDefaultSkin = window:getSkin()
        panel = window.Box
        textarea = panel.ScratchpadEditBox
        prevButton = panel.ScratchpadPrevButton
        nextButton = panel.ScratchpadNextButton
        insertCoordsBtn = panel.ScratchpadGetCoordsButton
        enterCoordsBtn = panel.ScratchpadEnterCoordsButton
        sendCoordsBtn = panel.ScratchpadSendCoordsButton
        clearCoordsBtn = panel.ScratchpadClearCoordsButton
        stopCoordsBtn = panel.ScratchpadStopCoordsButton

        section1 = panel.CoordSection1
        section2 = panel.CoordSection2
        section3 = panel.CoordSection3
        section4 = panel.CoordSection4
        section5 = panel.CoordSection5
        section6 = panel.CoordSection6
        section7 = panel.CoordSection7
        section8 = panel.CoordSection8
        section9 = panel.CoordSection9
        section10 = panel.CoordSection10
        section11 = panel.CoordSection11
        section12 = panel.CoordSection12
        section13 = panel.CoordSection13
        section14 = panel.CoordSection14
        section15 = panel.CoordSection15
        table.insert(sections, section1)
        table.insert(sections, section2)
        table.insert(sections, section3)
        table.insert(sections, section4)
        table.insert(sections, section5)
        table.insert(sections, section6)
        table.insert(sections, section7)
        table.insert(sections, section8)
        table.insert(sections, section9)
        table.insert(sections, section10)
        table.insert(sections, section11)
        table.insert(sections, section12)
        table.insert(sections, section13)
        table.insert(sections, section14)
        table.insert(sections, section15)

        target1 = panel.CoordTarget1
        target2 = panel.CoordTarget2
        target3 = panel.CoordTarget3
        target4 = panel.CoordTarget4
        target5 = panel.CoordTarget5
        target6 = panel.CoordTarget6
        target7 = panel.CoordTarget7
        target8 = panel.CoordTarget8
        target9 = panel.CoordTarget9
        target10 = panel.CoordTarget10
        target11 = panel.CoordTarget11
        target12 = panel.CoordTarget12
        target13 = panel.CoordTarget13
        target14 = panel.CoordTarget14
        target15 = panel.CoordTarget15

        table.insert(targets, target1)
        table.insert(targets, target2)
        table.insert(targets, target3)
        table.insert(targets, target4)
        table.insert(targets, target5)
        table.insert(targets, target6)
        table.insert(targets, target7)
        table.insert(targets, target8)
        table.insert(targets, target9)
        table.insert(targets, target10)
        table.insert(targets, target11)
        table.insert(targets, target12)
        table.insert(targets, target13)
        table.insert(targets, target14)
        table.insert(targets, target15)

        -- setup textarea
        local skin = textarea:getSkin()
        skin.skinData.states.released[1].text.fontSize = scratchpad.config.fontSize
        textarea:setSkin(skin)

        scratchpad.log("Configuring callbacks...")
        textarea:addFocusCallback(
            function(self)
                if self:getFocused() then
                    lockKeyboardInput()
                else
                    unlockKeyboardInput(true)
                end
            end
        )
        textarea:addKeyDownCallback(
            function(self, keyName, unicode)
                if keyName == "escape" then
                    self:setFocused(false)
                    unlockKeyboardInput(true)
                end
            end
        )

        -- setup button callbacks
        prevButton:addMouseDownCallback(
            function(self)
                prevPage()
            end
        )
        nextButton:addMouseDownCallback(
            function(self)
                nextPage()
            end
        )
        insertCoordsBtn:addMouseDownCallback(
            function(self)
                local result = updateCoordinates()
                textarea:setText(result)
            end
        )

        enterCoordsBtn:addMouseDownCallback(
            function(self)
                local result = enterCoordinates()
            end
        )

        sendCoordsBtn:addMouseDownCallback(
            function(self)
                local result = sendCoordinates()
                clearCoordinates()
            end
        )

        clearCoordsBtn:addMouseDownCallback(
            function(self)
                local result = clearCoordinates()
            end
        )

        stopCoordsBtn:addMouseDownCallback(
            function(self)
                local result = stopCoordinates()
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
        nextPage()

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
        prevButton:setBounds(0, h - 120, 40, 20)
        nextButton:setBounds(40, h - 120, 40, 20)
        insertCoordsBtn:setBounds(105, h - 120, 50, 20)
        enterCoordsBtn:setBounds(160, h - 120, 50, 20)
        sendCoordsBtn:setBounds(210, h - 120, 50, 20)
        clearCoordsBtn:setBounds(265, h - 120, 50, 20)
        stopCoordsBtn:setBounds(265+55, h - 120, 50, 20)

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
        insertCoordsBtn:setVisible(true)

        -- show prev/next buttons only if we have more than one page
        prevButton:setVisible(true)
        nextButton:setVisible(true)

        isHidden = false
    end

    function scratchpad.hide()
        window:setSkin(windowSkinHidden)
        panel:setVisible(false)
        textarea:setFocused(false)
        window:setHasCursor(false)
        -- window.setVisible(false) -- if you make the window invisible, its destroyed
        unlockKeyboardInput(true)
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
