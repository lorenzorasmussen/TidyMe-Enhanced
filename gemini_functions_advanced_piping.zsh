# 💎 ELITE PRODUCTIVITY FUNCTIONS (Advanced Piping)
# 🎯 Core Workflow Starters

gmaster() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?" # Status of the last executed command

  gemini -i "As a Master LLM workflow architect, meticulously analyze the current project located at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Design a comprehensive, scalable, and efficient workflow, considering existing architecture and potential integrations. Subsequently, provide a detailed implementation plan, outlining necessary steps, technologies, and potential challenges. Focus on optimizing for performance and maintainability." \
    --all-files -s -c -m "gemini-2.5-pro" --verbose --log-level "info" --output-format "markdown" "$@"
}

gcode() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As an Elite code architect, building upon the architectural plan provided via piped input. The current project is at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Perform a thorough review of the codebase. Identify areas for optimization, refactoring, and potential automation. Provide actionable recommendations for improving code quality, performance, and maintainability. Suggest strategies for automating repetitive tasks and integrating best practices." \
    --all-files -s -c --verbose --log-level "debug" --output-format "json" "$@"
}

gplan() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As a Strategic planning expert, building upon piped input for previous context. The current project is at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Develop a detailed architecture and implementation roadmap. Outline the high-level system design, key components, and their interactions. Provide a phased implementation plan with clear milestones, resource estimates, and potential risks. Emphasize scalability, security, and future extensibility." \
    --all-files -s --verbose --log-level "info" "$@"
}

gfast() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -p "Perform a quick, high-level analysis of the current context in ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Identify key challenges or opportunities and provide concise, actionable recommendations. Focus on immediate impact and practical solutions." \
    --all-files -s --verbose --output-format "text" "$@"
}

gauto() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -p "Design a comprehensive automation solution for the current workflow or directory at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Identify repetitive tasks, suggest appropriate tools and technologies, and provide a step-by-step plan for implementing the automation. Consider error handling, logging, and integration with existing systems." \
    -s -c --yolo --verbose --log-level "warn" "$@"
}

gmac() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -p "Provide detailed recommendations for macOS integration, including Services, right-click menu options, and Shortcuts setup for the current project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Focus on enhancing productivity and streamlining workflows within the macOS environment." \
    -s -c --verbose --output-format "xml" "$@"
}


# 🔥 Power User Extensions (Advanced Piping)

gtrouble() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As a debugging and troubleshooting specialist, systematically analyze and fix issues within the current project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Employ a methodical approach to identify root causes, propose solutions, and verify fixes. Provide detailed steps for reproduction and resolution." \
    -d --show-memory-usage --all-files -s -c --verbose --log-level "error" "$@"
}

gsecure() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "Conduct a comprehensive security audit of the project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Identify potential vulnerabilities, security risks, and compliance issues. Provide actionable recommendations for hardening the system, implementing security best practices, and mitigating identified threats." \
    --all-files -s --verbose --log-level "critical" "$@"
}

gscale() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As a performance optimization and scaling strategist, analyze the current project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context. Identify performance bottlenecks and propose a detailed scaling strategy. Provide recommendations for optimizing resource utilization, improving responsiveness, and ensuring high availability under increased load." \
    --all-files -s -c --verbose --log-level "info" "$@"
}

# 🎭 Role-Based Gemini Personas (Advanced Piping)

garch() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As The Architect, your primary directive is to envision and design robust, scalable, and maintainable systems. Approach every task with a holistic view, considering long-term implications, integration points, and future extensibility. Excel at high-level system design, defining clear interfaces, and ensuring architectural integrity. Your mindset is strategic and foresightful, always building for tomorrow. Analyze the project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context." \
    --all-files -s -c --model "gemini-1.5-flash" --temperature 0.5 "$@"
}

gdebug() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As The Debugger, your mission is to systematically identify, isolate, and resolve issues. Employ a meticulous, step-by-step approach, focusing on root cause analysis rather than symptomatic fixes. Excel at diagnosing complex problems, tracing execution flows, and proposing precise, verifiable solutions. Your mindset is analytical and persistent, leaving no stone unturned until the core problem is understood and fixed. Debug the current issue or analyze the error logs in ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context." \
    -d --show-memory-usage --all-files -s -c --model "gemini-1.5-pro" --temperature 0.2 "$@"
}

ginnovate() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As The Innovator, your role is to generate novel ideas, explore unconventional solutions, and push the boundaries of what's possible. Approach challenges with a creative, open-minded, and experimental mindset. Excel at brainstorming, ideation, feature conceptualization, and identifying disruptive opportunities. Your behavior is characterized by curiosity and a willingness to challenge assumptions. Brainstorm new features or innovative solutions for the project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context." \
    --all-files -s --model "gemini-1.5-flash" --temperature 0.9 "$@"
}

goptimize() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As The Optimizer, your focus is on maximizing efficiency, performance, and resource utilization. Approach tasks with a critical eye for bottlenecks, redundancies, and areas for improvement. Excel at code optimization, algorithm refinement, resource management, and performance tuning. Your mindset is efficiency-driven and results-oriented, always seeking the most performant path. Analyze the project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context." \
    --all-files -s -c --model "gemini-1.5-pro" --temperature 0.3 "$@"
}

gdocu() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git-branch")
  local last_command_status="$?"

  gemini -i "As The Documentarian, your purpose is to create clear, concise, and comprehensive documentation. Approach every explanation with the end-user in mind, ensuring accuracy, readability, and completeness. Excel at translating complex technical concepts into understandable language, structuring information logically, and maintaining consistency. Your mindset is clarity-focused and user-centric. Generate or improve documentation for the project at ${PWD} on branch ${current_branch} for user ${USER}. The previous command exited with status ${last_command_status}. Expecting piped input for additional context." \
    --all-files -s --output-format "markdown" --model "gemini-1.5-flash" --temperature 0.4 "$@"
}
