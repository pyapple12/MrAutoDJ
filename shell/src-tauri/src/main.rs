// MrAutoDJ Tauri 壳（PL003.5）：spawn Python sidecar + 就绪握手（端口）+ 事件注入前端 + 退出清理
// 零业务纪律：本壳不含任何 DJ 业务逻辑；协议见 docs/ipc_protocol.md
//
// 安全说明：本文件仅以**编译期常量路径**启动固定程序（.venv 内解释器），
// Rust std::process::Command 不经过任何 shell（等价 shell=False 的参数列表形式），
// 全程无用户输入参与路径或参数构造。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{Emitter, Manager};

/// sidecar 启动参数（固定字面量：python -m modules.gateway）
const GATEWAY_ARGS: [&str; 2] = ["-m", "modules.gateway"];

/// sidecar 子进程句柄（退出时 kill）
struct Sidecar(Mutex<Option<Child>>);

/// 项目根目录：src-tauri → shell → 根（.venv 与 modules 所在）
/// 路径基准取自编译期常量 CARGO_MANIFEST_DIR，不含运行时输入。
fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf()
}

/// 解释器路径：项目根下固定的 .venv 内 python（常量子路径拼接）
fn python_path() -> PathBuf {
    project_root().join(".venv").join("Scripts").join("python.exe")
}

/// spawn gateway 并做就绪握手：读 stdout 的 "gateway ready port=<N>" 行 → emit 事件
fn spawn_gateway(app: &tauri::AppHandle) {
    let mut child = match Command::new(python_path())
        .args(GATEWAY_ARGS)
        .current_dir(project_root())
        .stdout(Stdio::piped())
        .spawn()
    {
        Ok(c) => c,
        Err(e) => {
            eprintln!("spawn gateway 失败: {e}");
            return;
        }
    };

    // 就绪握手：阻塞读 stdout 直到就绪行（gateway 启动后 stdout 无其他输出）
    let stdout = child.stdout.take().expect("stdout 已 piped");
    let mut port: Option<u16> = None;
    for line in BufReader::new(stdout).lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };
        if let Some(rest) = line.strip_prefix("gateway ready port=") {
            port = rest.trim().parse::<u16>().ok();
            break;
        }
    }

    match port {
        Some(p) => {
            eprintln!("gateway sidecar 就绪 port={p}");
            let _ = app.emit("gateway-port", p);
        }
        None => eprintln!("未读到 gateway ready 行（sidecar 异常？）"),
    }
    app.state::<Sidecar>().0.lock().unwrap().replace(child);
}

fn main() {
    tauri::Builder::default()
        .manage(Sidecar(Mutex::new(None)))
        .setup(|app| {
            // spawn 放独立线程（stdout 就绪行读取阻塞，不得卡 setup）
            let handle = app.handle().clone();
            std::thread::spawn(move || spawn_gateway(&handle));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("tauri 初始化失败")
        .run(|app, event| {
            // 应用退出：终止 sidecar（窗口关闭即整窗退出，单窗壳）
            if let tauri::RunEvent::Exit = event {
                if let Some(mut child) = app.state::<Sidecar>().0.lock().unwrap().take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
        });
}
