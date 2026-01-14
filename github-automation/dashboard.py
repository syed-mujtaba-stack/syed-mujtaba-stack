#!/usr/bin/env python3
"""
GitHub Contribution Dashboard
Monitor and visualize your contribution patterns
"""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List
import sys

class ContributionDashboard:
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.contribution_data = self.load_contribution_data()
    
    def load_contribution_data(self) -> Dict:
        """Load contribution data from git log"""
        try:
            # Get commit history
            result = subprocess.run(
                ["git", "log", "--oneline", "--since=30 days ago", "--pretty=format:%h|%s|%ai"],
                capture_output=True, text=True, shell=True
            )
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'date': parts[2]
                        })
            
            return {'commits': commits}
        except Exception as e:
            print(f"Error loading contribution data: {e}")
            return {'commits': []}
    
    def generate_dashboard(self) -> str:
        """Generate a visual dashboard"""
        commits = self.contribution_data['commits']
        
        # Analyze commit patterns
        commit_types = self.analyze_commit_types(commits)
        daily_activity = self.analyze_daily_activity(commits)
        weekly_pattern = self.analyze_weekly_pattern(commits)
        
        dashboard = f"""
# 📊 GitHub Contribution Dashboard

## 📈 Statistics Overview
- **Total Commits (30 days)**: {len(commits)}
- **Daily Average**: {len(commits) / 30:.1f}
- **Most Active Day**: {self.get_most_active_day(daily_activity)}
- **Current Streak**: {self.calculate_streak(commits)} days

## 🎯 Commit Types Distribution
{self.format_commit_types(commit_types)}

## 📅 Daily Activity Pattern
{self.format_daily_activity(daily_activity)}

## 📊 Weekly Pattern
{self.format_weekly_pattern(weekly_pattern)}

## 🔥 Recent Contributions
{self.format_recent_commits(commits[:10])}

## 💡 Insights
{self.generate_insights(commit_types, daily_activity, weekly_pattern)}

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return dashboard
    
    def analyze_commit_types(self, commits: List[Dict]) -> Dict[str, int]:
        """Analyze commit types from messages"""
        types = {
            'tutorial': 0,
            'example': 0,
            'docs': 0,
            'fix': 0,
            'ai': 0,
            'stats': 0,
            'other': 0
        }
        
        for commit in commits:
            message = commit['message'].lower()
            if 'tutorial' in message or '📚' in message:
                types['tutorial'] += 1
            elif 'example' in message or '💻' in message:
                types['example'] += 1
            elif 'docs' in message or '📝' in message:
                types['docs'] += 1
            elif 'fix' in message or '🔧' in message:
                types['fix'] += 1
            elif 'ai' in message or '🤖' in message:
                types['ai'] += 1
            elif 'stats' in message or '📊' in message:
                types['stats'] += 1
            else:
                types['other'] += 1
        
        return types
    
    def analyze_daily_activity(self, commits: List[Dict]) -> Dict[str, int]:
        """Analyze daily activity patterns"""
        daily = {}
        for commit in commits:
            date = commit['date'].split('T')[0]
            daily[date] = daily.get(date, 0) + 1
        return daily
    
    def analyze_weekly_pattern(self, commits: List[Dict]) -> Dict[str, int]:
        """Analyze weekly contribution patterns"""
        weekly = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # Sunday=0
        
        for commit in commits:
            date = datetime.fromisoformat(commit['date'].replace('Z', '+00:00'))
            weekly[date.weekday()] += 1
        
        return weekly
    
    def get_most_active_day(self, daily_activity: Dict[str, int]) -> str:
        """Find the most active day"""
        if not daily_activity:
            return "No data"
        
        max_commits = max(daily_activity.values())
        most_active_days = [day for day, count in daily_activity.items() if count == max_commits]
        return f"{most_active_days[0]} ({max_commits} commits)"
    
    def calculate_streak(self, commits: List[Dict]) -> int:
        """Calculate current contribution streak"""
        if not commits:
            return 0
        
        dates = sorted({commit['date'].split('T')[0] for commit in commits})
        today = datetime.now().date()
        streak = 0
        
        for i in range(len(dates) - 1, -1, -1):
            commit_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
            days_diff = (today - commit_date).days
            
            if days_diff == streak:
                streak += 1
            else:
                break
        
        return streak
    
    def format_commit_types(self, types: Dict[str, int]) -> str:
        """Format commit types for display"""
        total = sum(types.values())
        if total == 0:
            return "No commits to analyze"
        
        result = "| Type | Count | Percentage |\n|------|-------|------------|\n"
        for commit_type, count in types.items():
            if count > 0:
                percentage = (count / total) * 100
                emoji = self.get_type_emoji(commit_type)
                result += f"| {emoji} {commit_type.title()} | {count} | {percentage:.1f}% |\n"
        
        return result
    
    def format_daily_activity(self, daily_activity: Dict[str, int]) -> str:
        """Format daily activity for display"""
        if not daily_activity:
            return "No activity data"
        
        # Get last 7 days
        today = datetime.now().date()
        result = "| Date | Commits | Activity |\n|------|---------|----------|\n"
        
        for i in range(7):
            date = today - timedelta(days=6-i)
            date_str = date.strftime('%Y-%m-%d')
            commits = daily_activity.get(date_str, 0)
            activity = self.get_activity_bar(commits)
            result += f"| {date_str} | {commits} | {activity} |\n"
        
        return result
    
    def format_weekly_pattern(self, weekly_pattern: Dict[int, int]) -> str:
        """Format weekly pattern for display"""
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        result = "| Day | Commits | Pattern |\n|-----|---------|----------|\n"
        
        for day_index, day_name in enumerate(days):
            commits = weekly_pattern.get(day_index, 0)
            pattern = self.get_activity_bar(commits)
            result += f"| {day_name} | {commits} | {pattern} |\n"
        
        return result
    
    def format_recent_commits(self, commits: List[Dict]) -> str:
        """Format recent commits for display"""
        if not commits:
            return "No recent commits"
        
        result = "| Date | Message | Hash |\n|------|---------|------|\n"
        for commit in commits:
            date = commit['date'].split('T')[0]
            message = commit['message'][:50] + "..." if len(commit['message']) > 50 else commit['message']
            result += f"| {date} | {message} | {commit['hash']} |\n"
        
        return result
    
    def generate_insights(self, commit_types: Dict, daily_activity: Dict, weekly_pattern: Dict) -> str:
        """Generate insights from data"""
        insights = []
        
        # Most productive day
        if weekly_pattern:
            max_day = max(weekly_pattern, key=weekly_pattern.get)
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            insights.append(f"🎯 **Most productive day**: {day_names[max_day]} with {weekly_pattern[max_day]} commits")
        
        # Commit type preference
        if commit_types:
            max_type = max(commit_types, key=commit_types.get)
            if commit_types[max_type] > 0:
                insights.append(f"📝 **Favorite contribution type**: {max_type.title()} ({commit_types[max_type]} commits)")
        
        # Consistency check
        if daily_activity:
            recent_days = list(daily_activity.keys())[-7:]
            if len(recent_days) >= 5:
                insights.append("🔥 **Consistent contributor**: Active in 5+ of the last 7 days")
        
        # Diversity check
        active_types = sum(1 for count in commit_types.values() if count > 0)
        if active_types >= 4:
            insights.append("🌈 **Diverse contributor**: Using 4+ different contribution types")
        
        return "\n".join(insights) if insights else "Keep contributing to generate insights!"
    
    def get_type_emoji(self, commit_type: str) -> str:
        """Get emoji for commit type"""
        emojis = {
            'tutorial': '📚',
            'example': '💻',
            'docs': '📝',
            'fix': '🔧',
            'ai': '🤖',
            'stats': '📊',
            'other': '🚀'
        }
        return emojis.get(commit_type, '🚀')
    
    def get_activity_bar(self, count: int) -> str:
        """Generate activity bar based on count"""
        if count == 0:
            return "░░░░░"
        elif count <= 2:
            return "▓░░░░"
        elif count <= 4:
            return "▓▓░░░"
        elif count <= 6:
            return "▓▓▓░░"
        elif count <= 8:
            return "▓▓▓▓░"
        else:
            return "▓▓▓▓▓"
    
    def save_dashboard(self, filename: str = "dashboard.md"):
        """Save dashboard to file"""
        dashboard = self.generate_dashboard()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(dashboard)
        
        print(f"📊 Dashboard saved to {filename}")
        return filename

def main():
    """Main function to generate dashboard"""
    if len(sys.argv) < 3:
        print("Usage: python dashboard.py <repo_owner> <repo_name>")
        return
    
    repo_owner = sys.argv[1]
    repo_name = sys.argv[2]
    
    dashboard = ContributionDashboard(repo_owner, repo_name)
    filename = dashboard.save_dashboard()
    
    print(f"🎉 Dashboard generated successfully!")
    print(f"📁 File: {filename}")

if __name__ == "__main__":
    main()
