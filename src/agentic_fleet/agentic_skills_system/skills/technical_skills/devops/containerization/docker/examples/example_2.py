from capabilities.container_security_hardening import SecurityAuditor

auditor = SecurityAuditor('my-app-image:latest')
report = auditor.check_user()
print(report)