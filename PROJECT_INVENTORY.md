# Joseph Miller project inventory

This is the source inventory for project and experience content on socket23.com. It records work Joseph has explicitly confirmed and is written for a person-first portfolio.

## Publication rules

- Keep production environments anonymous.
- Do not add dates, employers, industries, organization sizes, project durations, or measured outcomes unless Joseph confirms them separately.
- Distinguish production work, personal lab work, research, and planned work.
- Describe Joseph’s contribution directly without implying sole ownership of a larger environment.
- Never publish internal addresses, credentials, recovery procedures, private topology, logs, or identifying configuration.

## Flagship project groups

### Enterprise VMware-to-Hyper-V migration using Veeam and Dell SAN storage

**Type:** Production infrastructure work

- Migrated production workloads from VMware ESXi to Windows Server 2025 Hyper-V.
- Used a temporary conversion host for staging and validation.
- Preserved VM identity, MAC addresses, disk layout, networking, and application availability.
- Performed isolated boot tests before controlled cutovers.
- Designed temporary and permanent storage layouts around an enterprise SAN.
- Configured SAS initiators, host groups, LUN mappings, MPIO, and read-only source access.
- Kept source VMFS LUNs offline and read-only in Windows.
- Used dedicated ReFS volumes for restored Hyper-V workloads.
- Configured a Hyper-V host as a Veeam-managed server and Direct SAN proxy.
- Restored multi-terabyte VMware virtual machines from SAN-backed datastores.
- Validated restore throughput, VHDX placement, checkpoints, guest services, and final production state.
- Migrated and validated Active Directory domain controllers, including DNS, SYSVOL, NETLOGON, FSMO ownership, replication, and static network identity.

### Local AI agent platform

**Type:** Personal lab and engineering work

- Built a local AI workstation around a high-memory professional NVIDIA GPU.
- Operated Ubuntu, NVIDIA drivers, CUDA, LM Studio, Ollama, llama.cpp, and vLLM.
- Hosted OpenAI-compatible APIs for controlled LAN and Tailscale access.
- Deployed OpenClaw Gateway in a Proxmox Ubuntu container and connected it to local models.
- Configured model aliases, context windows, API authentication, agent credentials, and SSH tunneling.
- Connected Hermes to local and hosted model providers, Tailscale, Telegram, and systemd.
- Evaluated model families, inference engines, memory use, context length, and quantization formats.
- Tested task-based routing between general and coding models.

### Network threat monitoring and forensics lab

**Type:** Personal security lab and research

- Built a Security Onion environment for packet capture, IDS alerts, Zeek logs, and Elastic investigation.
- Evaluated Security Onion alongside IPFire, Sophos, pfSense, and OPNsense environments.
- Deployed and analyzed DShield honeypot telemetry.
- Correlated attacker IPs, exploit attempts, ports, payload behavior, and CVE information.
- Used Zeek logs to analyze connections, DNS, HTTP, TLS, files, and anomalous traffic.
- Used SiLK to analyze source/destination relationships, ports, traffic volume, and unusual connections.
- Correlated IDS alerts with packet captures, network flows, endpoint activity, and threat intelligence.
- Built repeatable PCAP-analysis practice environments using Linux, Zeek, Wireshark, SiLK, and IDS tooling.
- Planned a CAPEv2 malware-analysis VM for Proxmox and integration with the monitoring stack.

### socket23.com self-hosting and secure delivery

**Type:** Public personal project

- Built and maintained the hosting stack for socket23.com using Cloudflare, Sophos, Docker Swarm, NGINX, DNS automation, and automated TLS.
- Troubleshot the complete path from public DNS through firewall policy to containers.
- Replaced mutable, root-run delivery with protected pull requests, CI, digest-addressed multi-architecture images, non-root containers, health checks, two replicas, runtime verification, and rollback.
- Automated wildcard certificate issuance with Dehydrated and Cloudflare DNS-01.
- Distributed certificates to containerized services and verified them with OpenSSL.

### Azure Virtual Desktop deployment and recovery automation

**Type:** Microsoft cloud work

- Deployed and repaired Azure Virtual Desktop session hosts.
- Diagnosed domain-join failures, registration issues, agent health, audio redirection, and profile problems.
- Used Azure PowerShell and deployment scripts for repeatable recovery.
- Built staged deployment modes with resource discovery, VM tracking, host-pool registration, and validation logs.

### Legacy Apple HFS+ data recovery

**Type:** Data recovery work

- Recovered data from an old PowerPC-era Mac disk image.
- Attached raw disk images, identified Apple HFS partitions, repaired journaled HFS+, and mounted encrypted sparse images.
- Copied recovered user data to modern storage with rsync.

### Network segmentation and secure remote access

**Type:** Networking and security work

- Audited a flat Juniper and Meraki network by mapping switch ports, VLAN membership, MAC addresses, and uplinks.
- Planned a low-risk VLAN cutover with requirements for console access, trunks, DHCP, gateways, and firewall policy.
- Configured Sophos XGS DNAT, SNAT, firewall rules, DNS forwarding, VPN routing, and service publishing.
- Used Tailscale for private management access to Linux hosts, Macs, agents, and security appliances.
- Connected a Wi-Fi Pineapple to Tailscale for authorized remote security-lab access and passive wireless collection research.

### Production-safe storage and recovery

**Type:** Production infrastructure and recovery work

- Developed a cautious workflow for discovering unknown SAN disks.
- Used Windows SAN Policy OfflineAll, disabled automount, and verified serial numbers before initializing targets.
- Prevented accidental write access to live VMFS volumes.
- Created dedicated ReFS volumes with 64 KB allocation units for Hyper-V and Veeam workloads.
- Designed folder structures for virtual machines, virtual disks, and restore staging.
- Performed isolated recovery tests and validated restore points, disk counts, application startup, networking, and final storage placement.

## Additional infrastructure, cloud, security, and automation work

### Infrastructure and virtualization

- Built and managed a multi-node Proxmox environment with ZFS, containers, virtual machines, bridges, scheduled backups, and Proxmox Backup Server.
- Tested VMware-to-Proxmox and VMware-to-Hyper-V conversion workflows for Windows and Linux workloads.
- Evaluated storage, boot mode, virtual hardware, network adapters, and disk-format compatibility.
- Planned migration of multi-terabyte file shares, permissions, data volumes, and dependent applications from an aging Windows server.
- Separated storage, SMB shares, applications, and domain services into explicit migration tracks.

### Networking and firewalls

- Diagnosed Sophos traffic flow with firewall logs, DNS tools, port tests, and scoped temporary rules.
- Migrated DNS hosting to Cloudflare and resolved stale records, IP changes, proxy behavior, and NAT interactions.
- Validated public service paths with dig, curl, and OpenSSL.
- Hosted web services with Docker Swarm and NGINX, including certificates, reverse proxying, deployments, and reloads.

### Cybersecurity and monitoring

- Investigated exploit attempts from honeypot and IDS telemetry and mapped activity to CVEs, affected services, and likely objectives.
- Practiced protocol and network-forensics analysis with Zeek, Wireshark, SiLK, PCAPs, and IDS data.
- Designed AI-assisted workflows for alert triage, attacker correlation, CVE enrichment, and incident reporting.

### Microsoft 365 and Azure

- Configured Exchange Online connectors for printers and scan-to-email, including SMTP routing, TLS, accepted senders, and source restrictions.
- Investigated Exchange Online archive capacity, provisioning, folder statistics, retention behavior, and visibility with PowerShell.
- Created and assigned Teams application access policies for an approved HubSpot recording and transcript integration.
- Diagnosed Conditional Access blocks involving location and grant controls while preserving broader policy enforcement.
- Repaired OneAuth, AAD Broker Plugin, OneDrive, Outlook, stale tenant mappings, account caches, SharePoint shortcuts, and profile-specific token state.

### Automation and systems administration

- Built repeatable PowerShell diagnostics for Active Directory, Hyper-V, Exchange Online, Azure, Windows networking, storage, and event logs.
- Used structured output and CSV exports to document findings.
- Validated Active Directory with repadmin, dcdiag, netdom, nltest, DNS tests, service checks, group membership, FSMO roles, and replication state.
- Investigated Windows bugchecks, kernel-power events, memory dumps, thermal sensors, and device health.
- Created private, external, and routed Hyper-V switches for isolated restored-server testing.
- Managed Ubuntu, Debian, Proxmox, Docker, systemd, SSH, storage mounts, packages, repositories, and interfaces.
- Implemented SSH keys, tunnels, Tailscale, firewall allowlists, and loopback-bound management services.

### Personal hybrid lab

- Built a lab spanning Proxmox, Windows Server, Active Directory, Security Onion, Docker, SAN storage, local AI, and multiple network zones.
- Used the environment for production-style validation, recovery testing, security research, and AI experimentation.
