# src/nlp/skill_dictionary.py

# Keep it simple now. You will expand over time.
# Normalize everything to lowercase in extraction stage.

TECH_SKILLS = [
    # Programming
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "php", "go", "rust", "kotlin", "swift",
    # Web
    "html", "css", "react", "angular", "vue", "node", "node.js", "express", "next.js",
    # Data/ML
    "sql", "mysql", "postgresql", "mongodb", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "nlp", "machine learning", "data science", "power bi", "tableau", "excel",
    # Cloud/DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "git", "github", "linux",
    # Mobile
    "android", "ios", "flutter", "react native",
    # Testing
    "selenium", "junit", "pytest",
    # Networking/Security
    "networking", "cybersecurity", "information security",
    # Tools
    "jira", "figma"
]

SOFT_SKILLS = [
    "communication", "teamwork", "problem solving", "leadership", "time management",
    "critical thinking", "presentation", "adaptability", "collaboration"
]