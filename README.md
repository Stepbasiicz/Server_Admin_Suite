# 🛡️ Soft4U Server Admin & Security Audit Suite 2026
> **Enterprise Desktop GUI for System Administrators & DevOps**  
> พัฒนาตามมาตรฐาน **Soft4UApp Enterprise Architecture Standard (Ultimate Master Blueprint 2026+)**

---

## 🌟 ฟังก์ชันหลัก (Core Features)

1. **🌐 เครื่องมือทดสอบเครือข่ายระดับสูง (Network Diagnostics & Port Scanner)**:
   - ทดสอบ **Ping** วัดค่า Latency (ms), Packet Loss (%) และคุณภาพการเชื่อมต่อ
   - **Visual Traceroute** ติดตาม Hop เส้นทางเครือข่ายและตรวจจับจุดคอขวด
   - **Multi-Threaded Port Scanner** ตรวจสอบพอร์ตมาตรฐานและพอร์ตสำคัญ (21, 22, 23, 25, 53, 80, 443, 3306, 5432, 6379, ฯลฯ) พร้อมประเมินระดับความเสี่ยงของพอร์ตที่เปิดทิ้งไว้

2. **🐧 การตรวจสอบสุขภาพและความปลอดภัยของ Linux Server ผ่าน SSH**:
   - เชื่อมต่อผ่าน SSH Port 22 (รองรับ User/Password และ SSH Private Key)
   - สรุปข้อมูลระบบปฏิบัติการ: Distro, Kernel, Architecture, Hostname, Uptime และ Load Average
   - ตรวจวัดทรัพยากร: CPU Cores, RAM (Total/Used/Free/%), Swap Space
   - ตรวจสอบพื้นที่ดิสก์ (`df -h`) ทุก Mount Point แจ้งเตือนเมื่อใช้งานเกิน 80% (Warning) หรือ 90% (Critical)
   - **ตรวจสอบสถานะ Firewall**: ตรวจ UFW, Firewalld, และ IPTables ประเมินว่าเปิดใช้งาน (Pass) หรือปิดทิ้งไว้เสี่ยงโดนโจมตี (Critical Fail)
   - **ตรวจสอบการอัปเดตแพตช์ความปลอดภัย**: ตรวจสอบ APT (Debian/Ubuntu) หรือ DNF/YUM (RHEL/CentOS) นับจำนวนแพตช์ค้างและแพตช์ความปลอดภัย (Security Updates)
   - ตรวจสอบการตั้งค่าความปลอดภัย SSH (PermitRootLogin, PasswordAuth)
   - มีกล่อง **Exec Command Helper** สำหรับรันคำสั่ง Linux ด่วนและดูผลลัพธ์ทันที

3. **🗄️ ตรวจสอบสุขภาพและความปลอดภัยของ MySQL / MariaDB Database**:
   - ทดสอบการเชื่อมต่อและดึงสเปก Engine, Version, Uptime, Threads Connected, Buffer Pool
   - คำนวณขนาดพื้นที่จัดเก็บของแต่ละฐานข้อมูล (Database Schemas Size MB) และนับจำนวนตาราง
   - ดูรายการ Processlist และคิวรีที่กำลังทำงาน
   - ตรวจสอบความปลอดภัย DB เชิงลึก:
     - ตรวจสอบว่าบัญชี `root` เปิดให้ล็อกอินจากทางไกล (`host='%'`) หรือไม่ (Critical Risk)
     - ตรวจสอบบัญชีผู้ใช้ที่ไม่มีรหัสผ่าน (Empty Password Accounts)
     - ตรวจสอบสถานะ Binary Logging (`log_bin`) สำหรับการกู้คืนข้อมูล

4. **📄 ออกรายงานการประเมินความปลอดภัยระดับบริหารเป็นไฟล์ PDF (Executive Audit Report)**:
   - ออกรายงาน PDF A4 ดีไซน์สวยงาม ได้มาตรฐานส่งผู้บริหาร / ฝ่ายไอที / กรรมการตรวจรับงาน / IT Audit (HA, ISO 27001, PDPA)
   - มี **Overall Security Score (0-100)** และเกรดความปลอดภัย (A+, A, B, C, F)
   - ตารางสรุปผล Pass / Warning / Critical Fail ทุกมิติ
   - สรุปรายการทรัพยากรฮาร์ดแวร์, รายการพอร์ตที่เปิด, รายการดิสก์, สรุปฐานข้อมูล และช่องลงนามผู้ตรวจสอบ (Sign-off)

5. **🔐 ความปลอดภัยระดับ Enterprise (Dual-Layer Vault & Privacy Masking)**:
   - รหัสผ่าน SSH และ MySQL เข้ารหัสสองชั้นด้วย **AES-256-GCM** + บีบอัด **zlib Level 9** บันทึกเป็นไบนารีไฟล์ `config.dat`
   - ช่องกรอกรหัสผ่านทุกช่องถูก Masked ด้วย `show="*"` พร้อมปุ่มสลับการมองเห็น (Eye Toggle `👁️` / `🙈`) ตามมาตรฐาน PDPA
   - Single-Instance Mutex ป้องกันการเปิดโปรแกรมซ้ำซ้อน
   - Dynamic Thai Font Resolver (Leelawadee UI / Sarabun / Tahoma)

---

## 🚀 วิธีการรันโปรแกรมบน Windows

```cmd
:: 1. เข้าไปในโฟลเดอร์โปรเจกต์
cd "G:\My Drive\Myprojects\server_admin_tool"

:: 2. รันผ่าน Batch script
run_app.bat

:: หรือรันผ่าน Python โดยตรง
python main.py
```

## 🔨 วิธีคอมไพล์เป็นไฟล์ Single .EXE

```cmd
build_windows_exe.bat
```
ไฟล์ EXE จะถูกสร้างไว้ที่โฟลเดอร์ `dist\Server_Admin_Suite\`
