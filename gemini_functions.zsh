# Helper function to get the prompt for a given role
_gemini_get_role_prompt() {
  local role_name="$1"
  local previous_context_summary="$2" # Context from the previous role

  # Define prompts for each role. Use ${previous_context_summary} where applicable.
  case "${role_name}" in
    "gmaster")
      echo "As a Master LLM workflow architect, meticulously analyze the current project located at ${PWD} for user ${USER}. Design a comprehensive, scalable, and efficient workflow, considering existing architecture and potential integrations. Subsequently, provide a detailed implementation plan, outlining necessary steps, technologies, and potential challenges. Focus on optimizing for performance and maintainability."
      ;;
    "gcode")
      echo "As an Elite code architect, building upon the previous context: ${previous_context_summary}. Perform a thorough review of the codebase in ${PWD} for user ${USER}. Identify areas for optimization, refactoring, and potential automation. Provide actionable recommendations for improving code quality, performance, and maintainability. Suggest strategies for automating repetitive tasks and integrating best practices."
      ;;
    "gplan")
      echo "As a Strategic planning expert, building upon the previous context: ${previous_context_summary}. Develop a detailed architecture and implementation roadmap for the project at ${PWD} for user ${USER}. Outline the high-level system design, key components, and their interactions. Provide a phased implementation plan with clear milestones, resource estimates, and potential risks. Emphasize scalability, security, and future extensibility."
      ;;
    "gfast")
      echo "Perform a quick, high-level analysis of the current context in ${PWD} for user ${USER}. Identify key challenges or opportunities and provide concise, actionable recommendations. Focus on immediate impact and practical solutions."
      ;;
    "gauto")
      echo "Design a comprehensive automation solution for the current workflow or directory at ${PWD} for user ${USER}. Identify repetitive tasks, suggest appropriate tools and technologies, and provide a step-by-step plan for implementing the automation. Consider error handling, logging, and integration with existing systems."
      ;;
    "gmac")
      echo "Provide detailed recommendations for macOS integration, including Services, right-click menu options, and Shortcuts setup for the current project at ${PWD} for user ${USER}. Focus on enhancing productivity and streamlining workflows within the macOS environment."
      ;;
    "gtrouble")
      echo "As a debugging and troubleshooting specialist, systematically analyze and fix issues within the current project at ${PWD} for user ${USER}. Employ a methodical approach to identify root causes, propose solutions, and verify fixes. Provide detailed steps for reproduction and resolution."
      ;;
    "gsecure")
      echo "Conduct a comprehensive security audit of the project at ${PWD} for user ${USER}. Identify potential vulnerabilities, security risks, and compliance issues. Provide actionable recommendations for hardening the system, implementing security best practices, and mitigating identified threats."
      ;;
    "gscale")
      echo "As a performance optimization and scaling strategist, analyze the current project at ${PWD} for user ${USER}. Identify performance bottlenecks and propose a detailed scaling strategy. Provide recommendations for optimizing resource utilization, improving responsiveness, and ensuring high availability under increased load."
      ;;
    "garch")
      echo "As The Architect, your primary directive is to envision and design robust, scalable, and maintainable systems. Approach every task with a holistic view, considering long-term implications, integration points, and future extensibility. Excel at high-level system design, defining clear interfaces, and ensuring architectural integrity. Your mindset is strategic and foresightful, always building for tomorrow. Analyze the project at ${PWD} for user ${USER} and provide a comprehensive architectural blueprint or design review."
      ;;
    "gdebug")
      echo "As The Debugger, your mission is to systematically identify, isolate, and resolve issues. Employ a meticulous, step-by-step approach, focusing on root cause analysis rather than symptomatic fixes. Excel at diagnosing complex problems, tracing execution flows, and proposing precise, verifiable solutions. Your mindset is analytical and persistent, leaving no stone unturned until the core problem is understood and fixed. Debug the current issue or analyze the error logs in ${PWD} for user ${USER}."
      ;;
    "ginnovate")
      echo "As The Innovator, your role is to generate novel ideas, explore unconventional solutions, and push the boundaries of what's possible. Approach challenges with a creative, open-minded, and experimental mindset. Excel at brainstorming, ideation, feature conceptualization, and identifying disruptive opportunities. Your behavior is characterized by curiosity and a willingness to challenge assumptions. Brainstorm new features or innovative solutions for the project at ${PWD} for user ${USER}."
      ;;
    "goptimize")
      echo "As The Optimizer, your focus is on maximizing efficiency, performance, and resource utilization. Approach tasks with a critical eye for bottlenecks, redundancies, and areas for improvement. Excel at code optimization, algorithm refinement, resource management, and performance tuning. Your mindset is efficiency-driven and results-oriented, always seeking the most performant path. Analyze the project at ${PWD} for user ${USER} and propose optimizations for speed, memory, or resource usage."
      ;;
    "gdocu")
      echo "As The Documentarian, your purpose is to create clear, concise, and comprehensive documentation. Approach every explanation with the end-user in mind, ensuring accuracy, readability, and completeness. Excel at translating complex technical concepts into understandable language, structuring information logically, and maintaining consistency. Your mindset is clarity-focused and user-centric. Generate or improve documentation for the project at ${PWD} for user ${USER}."
      ;;
    *)
      echo "Error: Unknown role prompt for '${role_name}'." >&2
      return 1
      ;;
  esac
}

# Helper function for role transitions
_gemini_role_transition() {
  local next_role="$1"
  local previous_context_summary="$2" # Summary of what the previous role did

  local next_prompt=$(_gemini_get_role_prompt "${next_role}" "${previous_context_summary}")
  if [[ $? -ne 0 ]]; then
    return 1 # Error from _gemini_get_role_prompt
  fi

  local next_gemini_command_base="gemini --all-files -s -c" # Base command, will be customized

  # Customize gemini command base for specific roles
  case "${next_role}" in
    "gmaster")
      next_gemini_command_base+=" -m \"gemini-2.5-pro\" --verbose --log-level \"info\" --output-format \"markdown\""
      ;;
    "gcode")
      next_gemini_command_base+=" --verbose --log-level \"debug\" --output-format \"json\""
      ;;
    "gplan")
      next_gemini_command_base+=" --verbose --log-level \"info\""
      ;;
    "gfast")
      next_gemini_command_base+=" -p --verbose --output-format \"text\""
      ;;
    "gauto")
      next_gemini_command_base+=" --yolo --verbose --log-level \"warn\""
      ;;
    "gmac")
      next_gemini_command_base+=" --verbose --output-format \"xml\""
      ;;
    "gtrouble")
      next_gemini_command_base+=" -d --show-memory-usage --verbose --log-level \"error\""
      ;;
    "gsecure")
      next_gemini_command_base+=" --verbose --log-level \"critical\""
      ;;
    "gscale")
      next_gemini_command_base+=" --verbose --log-level \"info\""
      ;;
    "garch")
      next_gemini_command_base+=" --model \"gemini-1.5-flash\" --temperature 0.5"
      ;;
    "gdebug")
      next_gemini_command_base+=" -d --show-memory-usage --model \"gemini-1.5-pro\" --temperature 0.2"
      ;;
    "ginnovate")
      next_gemini_command_base+=" --model \"gemini-1.5-flash\" --temperature 0.9"
      ;;
    "goptimize")
      next_gemini_command_base+=" --model \"gemini-1.5-pro\" --temperature 0.3"
      ;;
    "gdocu")
      next_gemini_command_base+=" --output-format \"markdown\" --model \"gemini-1.5-flash\" --temperature 0.4"
      ;;
  esac

  echo "To continue this workflow as the '${next_role}' role, run the following command:"
  echo ""
  echo "${next_gemini_command_base} -i \"${next_prompt}\""
  echo ""
  echo "Context from previous role: ${previous_context_summary}"
  echo ""
  echo "Press Enter to acknowledge, or Ctrl+C to cancel."
  read -r
}

# 💎 ELITE PRODUCTIVITY FUNCTIONS
# 🎯 Core Workflow Starters

gmaster() {
  local current_prompt=$(_gemini_get_role_prompt "gmaster")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s -c -m \"gemini-2.5-pro\" --verbose --log-level \"info\" --output-format \"markdown\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Master LLM workflow architect analysis completed."
  else
    eval "${gemini_command}"
  fi
}

gcode() {
  local current_prompt=$(_gemini_get_role_prompt "gcode")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s -c --verbose --log-level \"debug\" --output-format \"json\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Elite code architect review completed."
  else
    eval "${gemini_command}"
  fi
}

gplan() {
  local current_prompt=$(_gemini_get_role_prompt "gplan")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s --verbose --log-level \"info\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Strategic planning roadmap generated."
  else
    eval "${gemini_command}"
  fi
}

gfast() {
  local current_prompt=$(_gemini_get_role_prompt "gfast")
  local gemini_command="gemini -p \"${current_prompt}\" --all-files -s --verbose --output-format \"text\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Quick analysis and recommendations provided."
  else
    eval "${gemini_command}"
  fi
}

gauto() {
  local current_prompt=$(_gemini_get_role_prompt "gauto")
  local gemini_command="gemini -p \"${current_prompt}\" -s -c --yolo --verbose --log-level \"warn\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Automation design completed."
  else
    eval "${gemini_command}"
  fi
}

gmac() {
  local current_prompt=$(_gemini_get_role_prompt "gmac")
  local gemini_command="gemini -p \"${current_prompt}\" -s -c --verbose --output-format \"xml\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "macOS integration recommendations provided."
  else
    eval "${gemini_command}"
  fi
}

# 🔥 Power User Extensions

gtrouble() {
  local current_prompt=$(_gemini_get_role_prompt "gtrouble")
  local gemini_command="gemini -i \"${current_prompt}\" -d --show-memory-usage --all-files -s -c --verbose --log-level \"error\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Debugging and issue resolution completed."
  else
    eval "${gemini_command}"
  fi
}

gsecure() {
  local current_prompt=$(_gemini_get_role_prompt "gsecure")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s --verbose --log-level \"critical\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Security audit and hardening recommendations provided."
  else
    eval "${gemini_command}"
  fi
}

gscale() {
  local current_prompt=$(_gemini_get_role_prompt "gscale")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s -c --verbose --log-level \"info\""

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Performance optimization and scaling strategy developed."
  else
    eval "${gemini_command}"
  fi
}

# 🎭 Role-Based Gemini Personas (New)

garch() {
  local current_prompt=$(_gemini_get_role_prompt "garch")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s -c --model \"gemini-1.5-flash\" --temperature 0.5"

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Architectural design/review completed."
  else
    eval "${gemini_command}"
  fi
}

gdebug() {
  local current_prompt=$(_gemini_get_role_prompt "gdebug")
  local gemini_command="gemini -i \"${current_prompt}\" -d --show-memory-usage --all-files -s -c --model \"gemini-1.5-pro\" --temperature 0.2"

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Debugging session completed."
  else
    eval "${gemini_command}"
  fi
}

ginnovate() {
  local current_prompt=$(_gemini_get_role_prompt "ginnovate")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s --model \"gemini-1.5-flash\" --temperature 0.9"

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Innovation brainstorming completed."
  else
    eval "${gemini_command}"
  fi
}

goptimize() {
  local current_prompt=$(_gemini_get_role_prompt "goptimize")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s -c --model \"gemini-1.5-pro\" --temperature 0.3"

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Optimization analysis completed."
  else
    eval "${gemini_command}"
  fi
}

gdocu() {
  local current_prompt=$(_gemini_get_role_prompt "gdocu")
  local gemini_command="gemini -i \"${current_prompt}\" --all-files -s --output-format \"markdown\" --model \"gemini-1.5-flash\" --temperature 0.4"

  if [[ -n "$1" ]]; then
    _gemini_role_transition "$1" "Documentation generation completed."
  else
    eval "${gemini_command}"
  fi
}
