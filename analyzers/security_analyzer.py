"""
Code Analytics - Security Analyzer
Checks for common security issues and vulnerabilities
"""

import re
from typing import Dict, List, Any


class SecurityAnalyzer:
    """Analyze code for security issues"""

    # Common security patterns to check
    SECURITY_PATTERNS = {
        "python": {
            "sql_injection": [
                (r'execute\s*\(\s*["\'].*%s', "Possible SQL injection using string formatting"),
                (r'execute\s*\(\s*f["\']', "Possible SQL injection using f-string"),
                (r'execute\s*\(\s*["\'].*\+', "Possible SQL injection using string concatenation"),
                (r"cursor\.execute\s*\([^,]+\+", "SQL query built with concatenation"),
            ],
            "command_injection": [
                (r"os\.system\s*\(", "Use of os.system() - consider subprocess instead"),
                (r"subprocess\.call\s*\([^,]+shell\s*=\s*True", "Shell=True with subprocess is dangerous"),
                (r"subprocess\.Popen\s*\([^,]+shell\s*=\s*True", "Shell=True with subprocess is dangerous"),
                (r"eval\s*\(", "Use of eval() - potential code injection"),
                (r"exec\s*\(", "Use of exec() - potential code injection"),
            ],
            "hardcoded_secrets": [
                (r'password\s*=\s*["\'][^"\']+["\']', "Possible hardcoded password"),
                (r'api_key\s*=\s*["\'][^"\']+["\']', "Possible hardcoded API key"),
                (r'secret\s*=\s*["\'][^"\']+["\']', "Possible hardcoded secret"),
                (r'token\s*=\s*["\'][^"\']+["\']', "Possible hardcoded token"),
                (r"AWS_ACCESS_KEY", "Possible AWS credentials"),
                (r"PRIVATE_KEY", "Possible private key"),
            ],
            "unsafe_deserialization": [
                (r"pickle\.loads?\s*\(", "Pickle deserialization - untrusted data is dangerous"),
                (r"yaml\.load\s*\([^,]+\)", "Use yaml.safe_load() instead of yaml.load()"),
                (r"marshal\.loads?\s*\(", "Marshal deserialization is unsafe"),
            ],
            "path_traversal": [
                (r"open\s*\([^)]*\+[^)]*\)", "File open with concatenation - possible path traversal"),
            ],
            "weak_crypto": [
                (r"md5\s*\(", "MD5 is cryptographically weak - use SHA-256+"),
                (r"sha1\s*\(", "SHA1 is cryptographically weak - use SHA-256+"),
                (r"DES\s*\(", "DES encryption is weak - use AES"),
            ],
            "insecure_random": [
                (r"random\.random\s*\(", "random.random() not cryptographically secure - use secrets module"),
                (r"random\.randint\s*\(", "random.randint() not cryptographically secure - use secrets module"),
            ],
            "debug_code": [
                (r"print\s*\(.*password", "Printing password information"),
                (r"DEBUG\s*=\s*True", "Debug mode enabled"),
                (r"\.set_trace\s*\(", "Debugger breakpoint in code"),
            ],
        },
        "javascript": {
            "xss": [
                (r"innerHTML\s*=", "innerHTML assignment - possible XSS"),
                (r"document\.write\s*\(", "document.write() - possible XSS"),
                (r"\.html\s*\([^)]+\+", "jQuery .html() with concatenation - possible XSS"),
            ],
            "eval": [
                (r"eval\s*\(", "Use of eval() - potential code injection"),
                (r"new\s+Function\s*\(", "new Function() is similar to eval"),
                (r'setTimeout\s*\(\s*["\']', "setTimeout with string - similar to eval"),
                (r'setInterval\s*\(\s*["\']', "setInterval with string - similar to eval"),
            ],
            "hardcoded_secrets": [
                (r'apiKey\s*[:=]\s*["\'][^"\']+["\']', "Possible hardcoded API key"),
                (r'password\s*[:=]\s*["\'][^"\']+["\']', "Possible hardcoded password"),
                (r'secret\s*[:=]\s*["\'][^"\']+["\']', "Possible hardcoded secret"),
            ],
            "prototype_pollution": [
                (r"__proto__", "Prototype pollution risk"),
                (r"constructor\s*\[", "Possible prototype pollution"),
            ],
        },
        "general": {
            "sensitive_data": [
                (r"(?i)password", "Reference to password"),
                (r"(?i)api[_-]?key", "Reference to API key"),
                (r"(?i)secret[_-]?key", "Reference to secret key"),
                (r"(?i)auth[_-]?token", "Reference to auth token"),
                (r"(?i)private[_-]?key", "Reference to private key"),
            ],
            "ip_addresses": [
                (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "Hardcoded IP address"),
            ],
            "urls": [
                (r"http://(?!localhost)", "HTTP URL (not HTTPS)"),
            ],
        },
    }

    def __init__(self, code: str, language: str = "unknown"):
        self.code = code
        self.language = language.lower()
        self.lines = code.split("\n")

    def analyze(self) -> Dict[str, Any]:
        """Run full security analysis"""
        results = {"issues": [], "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}, "categories": {}}

        # Get language-specific patterns
        patterns_to_check = {}

        if self.language in self.SECURITY_PATTERNS:
            patterns_to_check.update(self.SECURITY_PATTERNS[self.language])

        patterns_to_check.update(self.SECURITY_PATTERNS["general"])

        # Check each pattern
        for category, patterns in patterns_to_check.items():
            category_issues = []

            for pattern, message in patterns:
                for i, line in enumerate(self.lines, 1):
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith(("#", "//", "/*", "*")):
                        continue

                    if re.search(pattern, line, re.IGNORECASE):
                        severity = self._determine_severity(category, pattern)
                        issue = {
                            "line": i,
                            "category": category,
                            "message": message,
                            "severity": severity,
                            "code": line.strip()[:80],
                        }
                        category_issues.append(issue)
                        results["issues"].append(issue)
                        results["severity_counts"][severity] += 1

            if category_issues:
                results["categories"][category] = len(category_issues)

        results["total_issues"] = len(results["issues"])
        results["risk_score"] = self._calculate_risk_score(results)

        return results

    def _determine_severity(self, category: str, pattern: str) -> str:
        """Determine severity of a security issue"""
        critical_categories = ["sql_injection", "command_injection", "unsafe_deserialization"]
        high_categories = ["xss", "eval", "prototype_pollution", "hardcoded_secrets"]
        medium_categories = ["weak_crypto", "path_traversal"]

        if category in critical_categories:
            return "critical"
        elif category in high_categories:
            return "high"
        elif category in medium_categories:
            return "medium"
        return "low"

    def _calculate_risk_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall risk score (0-100)"""
        weights = {"critical": 25, "high": 15, "medium": 5, "low": 2}

        score = 0
        for severity, count in results["severity_counts"].items():
            score += count * weights.get(severity, 1)

        return min(score, 100)

    def find_sensitive_data(self) -> List[Dict[str, Any]]:
        """Find potentially sensitive data in code"""
        sensitive_patterns = [
            (r'(?i)password\s*[:=]\s*["\'][^"\']{4,}["\']', "password", "high"),
            (r'(?i)api[_-]?key\s*[:=]\s*["\'][^"\']{10,}["\']', "api_key", "high"),
            (r'(?i)secret\s*[:=]\s*["\'][^"\']{8,}["\']', "secret", "high"),
            (r'(?i)token\s*[:=]\s*["\'][^"\']{10,}["\']', "token", "high"),
            (r"[a-zA-Z0-9+/]{40,}={0,2}", "base64_string", "medium"),
            (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "private_key", "critical"),
            (r"AKIA[0-9A-Z]{16}", "aws_access_key", "critical"),
        ]

        findings = []
        for i, line in enumerate(self.lines, 1):
            for pattern, data_type, severity in sensitive_patterns:
                if re.search(pattern, line):
                    findings.append(
                        {
                            "line": i,
                            "type": data_type,
                            "severity": severity,
                            "preview": line.strip()[:50] + "..." if len(line) > 50 else line.strip(),
                        }
                    )

        return findings

    def get_security_summary(self) -> str:
        """Get human-readable security summary"""
        results = self.analyze()

        if results["total_issues"] == 0:
            return "✅ No security issues detected"

        summary_parts = [f"⚠️ Found {results['total_issues']} potential security issues:"]

        if results["severity_counts"]["critical"] > 0:
            summary_parts.append(f"  🔴 Critical: {results['severity_counts']['critical']}")
        if results["severity_counts"]["high"] > 0:
            summary_parts.append(f"  🟠 High: {results['severity_counts']['high']}")
        if results["severity_counts"]["medium"] > 0:
            summary_parts.append(f"  🟡 Medium: {results['severity_counts']['medium']}")
        if results["severity_counts"]["low"] > 0:
            summary_parts.append(f"  🟢 Low: {results['severity_counts']['low']}")

        summary_parts.append(f"\nRisk Score: {results['risk_score']}/100")

        return "\n".join(summary_parts)
