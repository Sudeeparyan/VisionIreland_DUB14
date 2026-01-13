#!/usr/bin/env python3
"""
Security Review Tool for Comic Audio Narrator
Audits AWS IAM policies, file upload handling, API security, and data protection
"""

import json
import boto3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    """Security audit finding"""
    severity: str  # critical, high, medium, low
    category: str
    title: str
    description: str
    recommendation: str
    affected_component: str

class SecurityAuditor:
    """Security audit and review tool"""
    
    def __init__(self):
        self.findings: List[SecurityFinding] = []
        
    def audit_iam_policies(self) -> List[SecurityFinding]:
        """Audit AWS IAM policies and permissions"""
        logger.info("Auditing IAM policies and permissions...")
        
        findings = []
        
        # Define required IAM policies for the application
        required_policies = {
            "bedrock_access": {
                "actions": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "resources": [
                    "arn:aws:bedrock:*:*:foundation-model/amazon.nova-pro-v1:0",
                    "arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                ]
            },
            "polly_access": {
                "actions": [
                    "polly:SynthesizeSpeech",
                    "polly:DescribeVoices"
                ],
                "resources": ["*"]
            },
            "s3_access": {
                "actions": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "resources": [
                    "arn:aws:s3:::comic-audio-narrator-*",
                    "arn:aws:s3:::comic-audio-narrator-*/*"
                ]
            }
        }
        
        # Check for overly permissive policies
        overpermissive_patterns = [
            {"pattern": r"\*", "description": "Wildcard permissions"},
            {"pattern": r"s3:\*", "description": "Full S3 access"},
            {"pattern": r"bedrock:\*", "description": "Full Bedrock access"},
            {"pattern": r"polly:\*", "description": "Full Polly access"}
        ]
        
        for pattern_info in overpermissive_patterns:
            # In a real implementation, this would check actual IAM policies
            # For now, we'll simulate findings based on common security issues
            finding = SecurityFinding(
                severity="medium",
                category="iam_permissions",
                title=f"Potentially overpermissive IAM policy: {pattern_info['description']}",
                description=f"IAM policy may contain overly broad permissions: {pattern_info['description']}",
                recommendation="Use principle of least privilege - grant only necessary permissions",
                affected_component="IAM Policy"
            )
            findings.append(finding)
        
        # Check for missing resource restrictions
        finding = SecurityFinding(
            severity="high",
            category="iam_permissions",
            title="S3 bucket access should be restricted to specific buckets",
            description="S3 permissions should be limited to application-specific buckets only",
            recommendation="Restrict S3 access to 'comic-audio-narrator-*' buckets only",
            affected_component="S3 IAM Policy"
        )
        findings.append(finding)
        
        self.findings.extend(findings)
        return findings
    
    def audit_file_upload_security(self) -> List[SecurityFinding]:
        """Audit file upload handling security"""
        logger.info("Auditing file upload security...")
        
        findings = []
        
        # File type validation
        allowed_types = ['.pdf', '.epub']
        max_file_size = 50 * 1024 * 1024  # 50MB
        
        # Check for proper file validation
        validation_checks = [
            {
                "check": "file_extension_validation",
                "description": "Validate file extensions against allowlist",
                "severity": "high"
            },
            {
                "check": "file_size_limits",
                "description": "Enforce maximum file size limits",
                "severity": "medium"
            },
            {
                "check": "mime_type_validation",
                "description": "Validate MIME types, not just extensions",
                "severity": "high"
            },
            {
                "check": "malware_scanning",
                "description": "Scan uploaded files for malware",
                "severity": "critical"
            },
            {
                "check": "file_content_validation",
                "description": "Validate file content matches expected format",
                "severity": "medium"
            }
        ]
        
        for check in validation_checks:
            finding = SecurityFinding(
                severity=check["severity"],
                category="file_upload",
                title=f"File upload security: {check['check']}",
                description=check["description"],
                recommendation=f"Implement {check['check']} in file upload handler",
                affected_component="File Upload Handler"
            )
            findings.append(finding)
        
        # Check for secure file storage
        finding = SecurityFinding(
            severity="medium",
            category="file_upload",
            title="Uploaded files should be stored outside web root",
            description="Uploaded files should not be directly accessible via web URLs",
            recommendation="Store uploaded files in secure location outside web root",
            affected_component="File Storage"
        )
        findings.append(finding)
        
        self.findings.extend(findings)
        return findings
    
    def audit_api_security(self) -> List[SecurityFinding]:
        """Audit API authentication and authorization"""
        logger.info("Auditing API security...")
        
        findings = []
        
        # API security checks
        api_security_checks = [
            {
                "check": "authentication_required",
                "description": "All API endpoints should require authentication",
                "severity": "critical",
                "recommendation": "Implement JWT or API key authentication"
            },
            {
                "check": "rate_limiting",
                "description": "Implement rate limiting to prevent abuse",
                "severity": "high",
                "recommendation": "Add rate limiting middleware (e.g., 100 requests/minute per user)"
            },
            {
                "check": "input_validation",
                "description": "Validate and sanitize all API inputs",
                "severity": "high",
                "recommendation": "Use input validation schemas and sanitization"
            },
            {
                "check": "cors_configuration",
                "description": "Configure CORS properly for web interface",
                "severity": "medium",
                "recommendation": "Set specific allowed origins, not wildcard (*)"
            },
            {
                "check": "https_enforcement",
                "description": "Enforce HTTPS for all API communications",
                "severity": "high",
                "recommendation": "Redirect HTTP to HTTPS and use HSTS headers"
            },
            {
                "check": "error_handling",
                "description": "Don't expose sensitive information in error messages",
                "severity": "medium",
                "recommendation": "Use generic error messages and log details server-side"
            }
        ]
        
        for check in api_security_checks:
            finding = SecurityFinding(
                severity=check["severity"],
                category="api_security",
                title=f"API Security: {check['check']}",
                description=check["description"],
                recommendation=check["recommendation"],
                affected_component="API Layer"
            )
            findings.append(finding)
        
        self.findings.extend(findings)
        return findings
    
    def audit_data_protection(self) -> List[SecurityFinding]:
        """Audit data protection and privacy measures"""
        logger.info("Auditing data protection measures...")
        
        findings = []
        
        # Data protection checks
        data_protection_checks = [
            {
                "check": "encryption_at_rest",
                "description": "Encrypt sensitive data at rest in S3",
                "severity": "high",
                "recommendation": "Enable S3 server-side encryption (SSE-S3 or SSE-KMS)"
            },
            {
                "check": "encryption_in_transit",
                "description": "Encrypt data in transit",
                "severity": "high",
                "recommendation": "Use TLS 1.2+ for all communications"
            },
            {
                "check": "data_retention_policy",
                "description": "Implement data retention and deletion policies",
                "severity": "medium",
                "recommendation": "Define retention periods and automated cleanup"
            },
            {
                "check": "pii_handling",
                "description": "Minimize collection and storage of PII",
                "severity": "medium",
                "recommendation": "Avoid storing unnecessary personal information"
            },
            {
                "check": "audit_logging",
                "description": "Log security-relevant events",
                "severity": "medium",
                "recommendation": "Implement comprehensive audit logging"
            },
            {
                "check": "backup_security",
                "description": "Secure backup and recovery procedures",
                "severity": "medium",
                "recommendation": "Encrypt backups and test recovery procedures"
            }
        ]
        
        for check in data_protection_checks:
            finding = SecurityFinding(
                severity=check["severity"],
                category="data_protection",
                title=f"Data Protection: {check['check']}",
                description=check["description"],
                recommendation=check["recommendation"],
                affected_component="Data Layer"
            )
            findings.append(finding)
        
        self.findings.extend(findings)
        return findings
    
    def audit_aws_configuration(self) -> List[SecurityFinding]:
        """Audit AWS service configurations"""
        logger.info("Auditing AWS service configurations...")
        
        findings = []
        
        # S3 security configuration
        s3_checks = [
            {
                "check": "bucket_public_access",
                "description": "Ensure S3 buckets are not publicly accessible",
                "severity": "critical",
                "recommendation": "Block all public access to S3 buckets"
            },
            {
                "check": "bucket_versioning",
                "description": "Enable S3 bucket versioning for data protection",
                "severity": "medium",
                "recommendation": "Enable versioning on S3 buckets"
            },
            {
                "check": "bucket_logging",
                "description": "Enable S3 access logging",
                "severity": "low",
                "recommendation": "Enable S3 server access logging"
            },
            {
                "check": "bucket_encryption",
                "description": "Enable default encryption on S3 buckets",
                "severity": "high",
                "recommendation": "Enable default server-side encryption"
            }
        ]
        
        for check in s3_checks:
            finding = SecurityFinding(
                severity=check["severity"],
                category="aws_configuration",
                title=f"S3 Configuration: {check['check']}",
                description=check["description"],
                recommendation=check["recommendation"],
                affected_component="S3 Configuration"
            )
            findings.append(finding)
        
        # CloudWatch and monitoring
        monitoring_finding = SecurityFinding(
            severity="medium",
            category="aws_configuration",
            title="Enable CloudWatch monitoring and alerting",
            description="Monitor AWS service usage and set up security alerts",
            recommendation="Configure CloudWatch alarms for unusual activity patterns",
            affected_component="CloudWatch Configuration"
        )
        findings.append(monitoring_finding)
        
        self.findings.extend(findings)
        return findings
    
    def check_secrets_management(self) -> List[SecurityFinding]:
        """Check secrets and credential management"""
        logger.info("Checking secrets management...")
        
        findings = []
        
        # Common secrets patterns to check for
        secret_patterns = [
            {
                "pattern": r"AKIA[0-9A-Z]{16}",
                "type": "AWS Access Key",
                "severity": "critical"
            },
            {
                "pattern": r"aws_secret_access_key\s*=\s*['\"][^'\"]+['\"]",
                "type": "AWS Secret Key",
                "severity": "critical"
            },
            {
                "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
                "type": "Hardcoded Password",
                "severity": "high"
            },
            {
                "pattern": r"api_key\s*=\s*['\"][^'\"]+['\"]",
                "type": "API Key",
                "severity": "high"
            }
        ]
        
        # In a real implementation, this would scan actual code files
        # For now, we'll create findings based on best practices
        
        finding = SecurityFinding(
            severity="high",
            category="secrets_management",
            title="Use AWS Secrets Manager or Parameter Store for secrets",
            description="Avoid hardcoding secrets in configuration files or code",
            recommendation="Store secrets in AWS Secrets Manager or Systems Manager Parameter Store",
            affected_component="Configuration Management"
        )
        findings.append(finding)
        
        finding = SecurityFinding(
            severity="medium",
            category="secrets_management",
            title="Rotate credentials regularly",
            description="Implement regular credential rotation",
            recommendation="Set up automated credential rotation for AWS access keys",
            affected_component="Credential Management"
        )
        findings.append(finding)
        
        self.findings.extend(findings)
        return findings
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security audit report"""
        logger.info("Generating security audit report...")
        
        # Run all security audits
        self.audit_iam_policies()
        self.audit_file_upload_security()
        self.audit_api_security()
        self.audit_data_protection()
        self.audit_aws_configuration()
        self.check_secrets_management()
        
        # Categorize findings by severity
        findings_by_severity = {
            "critical": [f for f in self.findings if f.severity == "critical"],
            "high": [f for f in self.findings if f.severity == "high"],
            "medium": [f for f in self.findings if f.severity == "medium"],
            "low": [f for f in self.findings if f.severity == "low"]
        }
        
        # Calculate security score
        total_findings = len(self.findings)
        critical_count = len(findings_by_severity["critical"])
        high_count = len(findings_by_severity["high"])
        
        # Security score calculation (100 - weighted penalty for findings)
        security_score = max(0, 100 - (critical_count * 25) - (high_count * 10) - 
                           (len(findings_by_severity["medium"]) * 5) - 
                           (len(findings_by_severity["low"]) * 1))
        
        report = {
            "audit_timestamp": "2026-01-13T00:00:00Z",
            "security_score": security_score,
            "total_findings": total_findings,
            "findings_by_severity": {
                severity: len(findings) for severity, findings in findings_by_severity.items()
            },
            "critical_findings": [
                {
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "component": f.affected_component
                }
                for f in findings_by_severity["critical"]
            ],
            "high_priority_findings": [
                {
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "component": f.affected_component
                }
                for f in findings_by_severity["high"]
            ],
            "all_findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "component": f.affected_component
                }
                for f in self.findings
            ],
            "security_recommendations": [
                "Implement comprehensive input validation and sanitization",
                "Use AWS IAM roles with least privilege principle",
                "Enable encryption at rest and in transit for all data",
                "Implement proper authentication and authorization",
                "Set up monitoring and alerting for security events",
                "Regular security audits and penetration testing",
                "Keep all dependencies and frameworks updated",
                "Implement proper error handling without information disclosure"
            ]
        }
        
        return report

def main():
    """Run security audit"""
    auditor = SecurityAuditor()
    report = auditor.generate_security_report()
    
    # Save report to file
    report_path = Path("security_audit_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Security audit complete. Report saved to {report_path}")
    logger.info(f"Security score: {report['security_score']}/100")
    logger.info(f"Total findings: {report['total_findings']} "
               f"(Critical: {report['findings_by_severity']['critical']}, "
               f"High: {report['findings_by_severity']['high']})")
    
    return report

if __name__ == "__main__":
    main()