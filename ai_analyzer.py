#!/usr/bin/env python3
"""
AI-powered analyzer for TidyMe cleanup operations
Provides intelligent suggestions and analysis for cleanup activities
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re


class CleanupAnalyzer:
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            db_path = os.path.join(data_dir, 'cleanup.db')
        self.db_path = db_path

    def get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def analyze_cleanup_patterns(self) -> Dict[str, Any]:
        """Analyze cleanup patterns and provide insights"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Get cleanup statistics
        cursor.execute("""
            SELECT
                action_type,
                COUNT(*) as count,
                SUM(file_size) as total_size,
                AVG(success) as success_rate
            FROM cleanup_log
            GROUP BY action_type
            ORDER BY count DESC
        """)

        patterns = {}
        for row in cursor.fetchall():
            action_type, count, total_size, success_rate = row
            patterns[action_type] = {
                'count': count,
                'total_size_cleaned': total_size or 0,
                'success_rate': success_rate or 0
            }

        conn.close()
        return patterns

    def suggest_cleanup_schedule(self) -> List[str]:
        """Suggest optimal cleanup schedule based on usage patterns"""
        patterns = self.analyze_cleanup_patterns()
        suggestions = []

        # Analyze cache cleanup patterns
        if 'cache_delete' in patterns:
            cache_data = patterns['cache_delete']
            if cache_data['count'] > 10:
                suggestions.append("Consider increasing cache cleanup frequency - high cache accumulation detected")
            elif cache_data['success_rate'] < 0.8:
                suggestions.append("Cache cleanup success rate is low - check permissions or disk space")

        # Analyze temp file cleanup
        if 'temp_delete' in patterns:
            temp_data = patterns['temp_delete']
            if temp_data['count'] > 20:
                suggestions.append("High temporary file generation detected - consider more frequent temp cleanup")
            if temp_data['total_size_cleaned'] > 1024 * 1024 * 1024:  # 1GB
                suggestions.append("Large temporary files detected - monitor applications creating temp files")

        # Analyze development cleanup
        if 'dev_delete' in patterns:
            dev_data = patterns['dev_delete']
            if dev_data['count'] > 5:
                suggestions.append("Active development detected - consider weekly dev cleanup schedule")

        # General suggestions
        if not patterns:
            suggestions.append("No cleanup history found - run initial cleanup scan to establish baseline")
        else:
            suggestions.append("Cleanup operations are running normally")

        return suggestions

    def analyze_duplicate_patterns(self) -> Dict[str, Any]:
        """Analyze duplicate file patterns"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Get duplicate statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_duplicates,
                COUNT(DISTINCT group_id) as unique_groups,
                AVG(file_size) as avg_file_size,
                SUM(file_size) as total_wasted_space
            FROM duplicates
        """)

        stats = cursor.fetchone()
        if stats:
            total_dup, unique_groups, avg_size, total_wasted = stats
        else:
            total_dup = unique_groups = avg_size = total_wasted = 0

        # Get file type distribution
        cursor.execute("""
            SELECT
                CASE
                    WHEN file_path LIKE '%.jpg' OR file_path LIKE '%.jpeg' OR file_path LIKE '%.png' OR file_path LIKE '%.gif' THEN 'Images'
                    WHEN file_path LIKE '%.mp4' OR file_path LIKE '%.avi' OR file_path LIKE '%.mov' THEN 'Videos'
                    WHEN file_path LIKE '%.mp3' OR file_path LIKE '%.wav' OR file_path LIKE '%.flac' THEN 'Audio'
                    WHEN file_path LIKE '%.pdf' OR file_path LIKE '%.doc' OR file_path LIKE '%.txt' THEN 'Documents'
                    ELSE 'Other'
                END as file_type,
                COUNT(*) as count
            FROM duplicates
            GROUP BY file_type
            ORDER BY count DESC
        """)

        type_distribution = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_duplicates': total_dup,
            'unique_groups': unique_groups,
            'average_file_size': avg_size or 0,
            'total_wasted_space': total_wasted or 0,
            'file_type_distribution': type_distribution
        }

    def generate_cleanup_report(self) -> str:
        """Generate comprehensive cleanup report with AI insights"""
        patterns = self.analyze_cleanup_patterns()
        duplicates = self.analyze_duplicate_patterns()
        suggestions = self.suggest_cleanup_schedule()

        report = []
        report.append("# 🧹 TidyMe AI Cleanup Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary statistics
        report.append("## 📊 Summary Statistics")
        report.append(f"- **Total Duplicates Found**: {duplicates['total_duplicates']}")
        report.append(f"- **Unique Duplicate Groups**: {duplicates['unique_groups']}")
        report.append(f"- **Total Wasted Space**: {self._format_bytes(duplicates['total_wasted_space'])}")
        report.append("")

        # Cleanup patterns
        if patterns:
            report.append("## 🔄 Cleanup Patterns")
            for action, data in patterns.items():
                success_rate = data['success_rate'] * 100
                report.append(f"- **{action}**: {data['count']} operations, "
                            f"{self._format_bytes(data['total_size_cleaned'])} cleaned, "
                            f"{success_rate:.1f}% success rate")
            report.append("")

        # File type distribution
        if duplicates['file_type_distribution']:
            report.append("## 📁 Duplicate File Types")
            for file_type, count in duplicates['file_type_distribution'].items():
                percentage = (count / duplicates['total_duplicates']) * 100
                report.append(f"- **{file_type}**: {count} files ({percentage:.1f}%)")
            report.append("")

        # AI Suggestions
        if suggestions:
            report.append("## 🤖 AI Recommendations")
            for suggestion in suggestions:
                report.append(f"- {suggestion}")
            report.append("")

        return "\n".join(report)

    def predict_cleanup_needs(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict future cleanup needs based on historical data"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Get historical cleanup data
        cursor.execute("""
            SELECT
                DATE(action_date) as date,
                action_type,
                COUNT(*) as count,
                SUM(file_size) as total_size
            FROM cleanup_log
            WHERE action_date >= date('now', '-30 days')
            GROUP BY DATE(action_date), action_type
            ORDER BY date DESC
        """)

        historical_data = cursor.fetchall()
        conn.close()

        if not historical_data:
            return {"prediction": "Insufficient historical data for prediction"}

        # Simple trend analysis
        predictions = {}
        for action_type in ['cache_delete', 'temp_delete', 'dev_delete']:
            action_data = [row for row in historical_data if row[1] == action_type]

            if len(action_data) >= 7:  # Need at least a week of data
                recent_avg = sum(row[2] for row in action_data[:7]) / 7
                predictions[action_type] = {
                    'daily_average': recent_avg,
                    'predicted_weekly': recent_avg * days_ahead,
                    'trend': 'increasing' if recent_avg > sum(row[2] for row in action_data[7:14]) / 7 else 'stable'
                }

        return {
            'predictions': predictions,
            'confidence': 'medium' if len(historical_data) > 50 else 'low'
        }

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable format"""
        if bytes_value == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return ".1f"
            bytes_value /= 1024.0
        return ".1f"

    def get_cleanup_insights(self) -> List[str]:
        """Get AI-powered insights about cleanup operations"""
        insights = []

        # Analyze recent activity
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM cleanup_log
            WHERE action_date >= datetime('now', '-1 hour')
        """)
        recent_activity = cursor.fetchone()[0]

        if recent_activity > 10:
            insights.append("High cleanup activity detected in the last hour - system may need optimization")

        # Check for failed operations
        cursor.execute("""
            SELECT COUNT(*) FROM cleanup_log
            WHERE success = 0 AND action_date >= datetime('now', '-24 hours')
        """)
        failed_ops = cursor.fetchone()[0]

        if failed_ops > 5:
            insights.append(f"{failed_ops} cleanup operations failed recently - check permissions and disk space")

        # Analyze duplicate growth
        cursor.execute("""
            SELECT COUNT(*) FROM duplicates
            WHERE scan_date >= datetime('now', '-7 days')
        """)
        recent_duplicates = cursor.fetchone()[0]

        if recent_duplicates > 100:
            insights.append("High duplicate file creation detected - consider more frequent scans")

        conn.close()

        if not insights:
            insights.append("Cleanup operations are running smoothly with no issues detected")

        return insights


# CLI interface for AI analyzer
if __name__ == "__main__":
    analyzer = CleanupAnalyzer()

    print("🧹 TidyMe AI Cleanup Analyzer")
    print("=" * 50)

    # Generate and display report
    report = analyzer.generate_cleanup_report()
    print(report)

    print("\n🤖 AI Insights:")
    insights = analyzer.get_cleanup_insights()
    for insight in insights:
        print(f"• {insight}")

    print("\n📈 Predictions for next 7 days:")
    predictions = analyzer.predict_cleanup_needs()
    if 'predictions' in predictions:
        for action, data in predictions['predictions'].items():
            print(f"• {action}: ~{data['predicted_weekly']:.0f} operations ({data['trend']} trend)")
    else:
        print(f"• {predictions['prediction']}")