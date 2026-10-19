import AppKit
import Darwin
import Foundation
import WebKit

private let expectedProduct = "DEX Quorum"
private let windowTitle = "DEX//QUORUM — Live Conversational Intelligence"

@main
struct ConversationLensWrapperMain {
    private static let appDelegate = AppDelegate()

    static func main() {
        let app = NSApplication.shared
        app.delegate = appDelegate
        app.setActivationPolicy(.regular)
        app.run()
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate, NSWindowDelegate {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var statusLabel: NSTextField!
    private var spinner: NSProgressIndicator!
    private var backendProcess: Process?
    private var activePort: Int = 8788
    private var activeURL: URL { URL(string: "http://127.0.0.1:\(activePort)/")! }
    private var healthURL: URL { URL(string: "http://127.0.0.1:\(activePort)/api/health")! }

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.appearance = NSAppearance(named: .darkAqua)
        buildMenu()
        buildWindow()
        launchBackendAndConnect()
        NSApplication.shared.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window.makeKeyAndOrderFront(nil)
        sender.activate(ignoringOtherApps: true)
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        guard let backendProcess, backendProcess.isRunning else { return }
        backendProcess.terminate()
    }

    @objc private func reloadPage() {
        webView.reload()
    }

    @objc private func openInBrave() {
        let braveURL = URL(fileURLWithPath: "/Applications/Brave Browser.app")
        if FileManager.default.fileExists(atPath: braveURL.path) {
            let task = Process()
            task.executableURL = URL(fileURLWithPath: "/usr/bin/open")
            task.arguments = ["-a", "Brave Browser", activeURL.absoluteString]
            try? task.run()
        } else {
            NSWorkspace.shared.open(activeURL)
        }
    }

    private func buildMenu() {
        let mainMenu = NSMenu()

        let appItem = NSMenuItem()
        mainMenu.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About \(expectedProduct)", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide \(expectedProduct)", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Quit \(expectedProduct)", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu

        let editItem = NSMenuItem()
        mainMenu.addItem(editItem)
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        editMenu.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "Z")
        editMenu.addItem(.separator())
        editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = editMenu

        let viewItem = NSMenuItem()
        mainMenu.addItem(viewItem)
        let viewMenu = NSMenu(title: "View")
        let reload = NSMenuItem(title: "Reload Conversation Lens", action: #selector(reloadPage), keyEquivalent: "r")
        reload.target = self
        viewMenu.addItem(reload)
        let openBrave = NSMenuItem(title: "Open in Brave Browser", action: #selector(openInBrave), keyEquivalent: "B")
        openBrave.keyEquivalentModifierMask = [.command, .shift]
        openBrave.target = self
        viewMenu.addItem(openBrave)
        viewMenu.addItem(.separator())
        viewMenu.addItem(withTitle: "Enter Full Screen", action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f")
        viewItem.submenu = viewMenu

        NSApplication.shared.mainMenu = mainMenu
    }

    private func buildWindow() {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.mediaTypesRequiringUserActionForPlayback = []

        webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.translatesAutoresizingMaskIntoConstraints = false
        webView.isHidden = true

        spinner = NSProgressIndicator()
        spinner.style = .spinning
        spinner.controlSize = .regular
        spinner.translatesAutoresizingMaskIntoConstraints = false
        spinner.startAnimation(nil)

        statusLabel = NSTextField(labelWithString: "Starting DEX Quorum local engine…")
        statusLabel.textColor = .secondaryLabelColor
        statusLabel.font = .monospacedSystemFont(ofSize: 13, weight: .medium)
        statusLabel.translatesAutoresizingMaskIntoConstraints = false

        let loadingView = NSView()
        loadingView.translatesAutoresizingMaskIntoConstraints = false
        loadingView.identifier = NSUserInterfaceItemIdentifier("loadingView")
        loadingView.addSubview(spinner)
        loadingView.addSubview(statusLabel)

        let contentView = NSView()
        contentView.wantsLayer = true
        contentView.layer?.backgroundColor = NSColor(calibratedRed: 0.04, green: 0.05, blue: 0.06, alpha: 1.0).cgColor
        contentView.addSubview(webView)
        contentView.addSubview(loadingView)

        NSLayoutConstraint.activate([
            webView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            webView.topAnchor.constraint(equalTo: contentView.topAnchor),
            webView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
            loadingView.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            loadingView.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            spinner.centerXAnchor.constraint(equalTo: loadingView.centerXAnchor),
            spinner.topAnchor.constraint(equalTo: loadingView.topAnchor),
            statusLabel.topAnchor.constraint(equalTo: spinner.bottomAnchor, constant: 12),
            statusLabel.leadingAnchor.constraint(equalTo: loadingView.leadingAnchor),
            statusLabel.trailingAnchor.constraint(equalTo: loadingView.trailingAnchor),
            statusLabel.bottomAnchor.constraint(equalTo: loadingView.bottomAnchor)
        ])

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1440, height: 920),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = windowTitle
        window.delegate = self
        window.minSize = NSSize(width: 820, height: 640)
        window.backgroundColor = NSColor(calibratedRed: 0.04, green: 0.05, blue: 0.06, alpha: 1.0)
        window.center()
        window.contentView = contentView
        window.makeKeyAndOrderFront(nil)
    }

    private func locateAppDirectory() -> URL? {
        let fm = FileManager.default
        if let override = ProcessInfo.processInfo.environment["CONVERSATION_LENS_DIR"], !override.isEmpty {
            let url = URL(fileURLWithPath: override, isDirectory: true)
            if fm.fileExists(atPath: url.appendingPathComponent("server.py").path) {
                return url
            }
        }
        let home = fm.homeDirectoryForCurrentUser
        let candidates = [
            home.appendingPathComponent("Conversation_Lens/Conversation_Lens_Intelligent_Speaker_v6", isDirectory: true),
            Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("Conversation_Lens_Intelligent_Speaker_v6", isDirectory: true)
        ]
        return candidates.first { fm.fileExists(atPath: $0.appendingPathComponent("server.py").path) }
    }

    private func isPortAvailable(_ port: Int) -> Bool {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { return false }
        defer { close(fd) }
        var addr = sockaddr_in()
        addr.sin_len = UInt8(MemoryLayout<sockaddr_in>.size)
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_port = in_port_t(UInt16(port).bigEndian)
        addr.sin_addr = in_addr(s_addr: inet_addr("127.0.0.1"))
        let bindResult = withUnsafePointer(to: &addr) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                Darwin.bind(fd, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        return bindResult == 0
    }

    private func pickAvailablePort() -> Int {
        for candidate in 8788...8815 {
            if isPortAvailable(candidate) {
                return candidate
            }
        }
        return 8788
    }

    private func ensureSpeakerSetupIfNeeded(in appDir: URL) {
        let fm = FileManager.default
        let speakerHome = fm.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/ConversationLensSpeakerID", isDirectory: true)
        let venvPy = speakerHome.appendingPathComponent("venv/bin/python")
        let onnxModel = speakerHome.appendingPathComponent("wespeaker_en_voxceleb_resnet34.onnx")
        if fm.isExecutableFile(atPath: venvPy.path) && fm.fileExists(atPath: onnxModel.path) {
            return
        }
        let setupScript = appDir.appendingPathComponent("Setup_Speakers.command")
        guard fm.isExecutableFile(atPath: setupScript.path) else { return }
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/zsh")
        task.arguments = [setupScript.path]
        task.currentDirectoryURL = appDir
        try? task.run()
        task.waitUntilExit()
    }

    private func launchBackendAndConnect() {
        guard let appDir = locateAppDirectory() else {
            showBlockingError(
                title: "DEX Quorum source not found",
                message: "Expected /Users/andrew/Conversation_Lens/Conversation_Lens_Intelligent_Speaker_v6/server.py."
            )
            return
        }

        activePort = pickAvailablePort()
        ensureSpeakerSetupIfNeeded(in: appDir)

        let logDir = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Logs/DexQuorum", isDirectory: true)
        try? FileManager.default.createDirectory(at: logDir, withIntermediateDirectories: true)
        let logURL = logDir.appendingPathComponent("server.log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)
        let logHandle = try? FileHandle(forWritingTo: logURL)

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = ["-u", appDir.appendingPathComponent("server.py").path, "--no-browser", "--port", "\(activePort)"]
        process.currentDirectoryURL = appDir
        var env = ProcessInfo.processInfo.environment
        let existingPath = env["PATH"] ?? "/usr/bin:/bin:/usr/sbin:/sbin"
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:\(existingPath)"
        env["PYTHONUNBUFFERED"] = "1"
        process.environment = env
        if let logHandle {
            process.standardOutput = logHandle
            process.standardError = logHandle
        }

        do {
            try process.run()
            backendProcess = process
            waitForBackend(attemptsRemaining: 60)
        } catch {
            showBlockingError(title: "Failed to start Conversation Lens server", message: error.localizedDescription)
        }
    }

    private func waitForBackend(attemptsRemaining: Int) {
        var req = URLRequest(url: healthURL)
        req.timeoutInterval = 1.0
        URLSession.shared.dataTask(with: req) { [weak self] data, response, _ in
            guard let self else { return }
            let ok = (response as? HTTPURLResponse)?.statusCode == 200 && data != nil
            DispatchQueue.main.async {
                if ok {
                    self.webView.load(URLRequest(url: self.activeURL))
                } else if attemptsRemaining > 0 {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                        self.waitForBackend(attemptsRemaining: attemptsRemaining - 1)
                    }
                } else {
                    self.showBlockingError(
                        title: "DEX Quorum server did not respond",
                        message: "Check ~/Library/Logs/DexQuorum/server.log for details."
                    )
                }
            }
        }.resume()
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        spinner.stopAnimation(nil)
        window.contentView?.subviews.first(where: { $0.identifier?.rawValue == "loadingView" })?.isHidden = true
        webView.isHidden = false
    }

    // Grant microphone capture inside native wrapper for localhost/127.0.0.1
    func webView(
        _ webView: WKWebView,
        requestMediaCapturePermissionFor origin: WKSecurityOrigin,
        initiatedByFrame frame: WKFrameInfo,
        type: WKMediaCaptureType,
        decisionHandler: @escaping (WKPermissionDecision) -> Void
    ) {
        if origin.host == "127.0.0.1" || origin.host == "localhost" {
            decisionHandler(.grant)
        } else {
            decisionHandler(.prompt)
        }
    }

    // Native confirm() dialog support (Stop Keep/Drop, Erase All, Protected Demo Load, Compaction)
    func webView(
        _ webView: WKWebView,
        runJavaScriptConfirmPanelWithMessage message: String,
        initiatedByFrame frame: WKFrameInfo,
        completionHandler: @escaping (Bool) -> Void
    ) {
        let alert = NSAlert()
        alert.messageText = expectedProduct
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Cancel")
        let response = alert.runModal()
        completionHandler(response == .alertFirstButtonReturn)
    }

    // Native alert() dialog support
    func webView(
        _ webView: WKWebView,
        runJavaScriptAlertPanelWithMessage message: String,
        initiatedByFrame frame: WKFrameInfo,
        completionHandler: @escaping () -> Void
    ) {
        let alert = NSAlert()
        alert.messageText = expectedProduct
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        alert.runModal()
        completionHandler()
    }

    // Native file-picker support (<input type="file"> for Restore snapshot & Import profiles)
    func webView(
        _ webView: WKWebView,
        runOpenPanelWith parameters: WKOpenPanelParameters,
        initiatedByFrame frame: WKFrameInfo,
        completionHandler: @escaping ([URL]?) -> Void
    ) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = parameters.allowsDirectories
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        if panel.runModal() == .OK {
            completionHandler(panel.urls)
        } else {
            completionHandler(nil)
        }
    }

    // Download support for Export Markdown, Export plain, Download session snapshot, Export profiles
    func webView(
        _ webView: WKWebView,
        decidePolicyFor navigationAction: WKNavigationAction,
        preferences: WKWebpagePreferences,
        decisionHandler: @escaping (WKNavigationActionPolicy, WKWebpagePreferences) -> Void
    ) {
        if navigationAction.shouldPerformDownload {
            decisionHandler(.download, preferences)
        } else {
            decisionHandler(.allow, preferences)
        }
    }

    func webView(
        _ webView: WKWebView,
        decidePolicyFor navigationResponse: WKNavigationResponse,
        decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void
    ) {
        if !navigationResponse.canShowMIMEType {
            decisionHandler(.download)
        } else {
            decisionHandler(.allow)
        }
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        download.delegate = self
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        download.delegate = self
    }

    func download(
        _ download: WKDownload,
        decideDestinationUsing response: URLResponse,
        suggestedFilename: String,
        completionHandler: @escaping (URL?) -> Void
    ) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedFilename
        panel.canCreateDirectories = true
        if panel.runModal() == .OK {
            completionHandler(panel.url)
        } else {
            completionHandler(nil)
        }
    }

    private func showBlockingError(title: String, message: String) {
        spinner.stopAnimation(nil)
        statusLabel.stringValue = "\(title): \(message)"
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = title
        alert.informativeText = message
        alert.runModal()
    }
}
