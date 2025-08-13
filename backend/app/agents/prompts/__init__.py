"""
Prompts package initialization
Provides easy access to prompt manager and utilities
"""

from .prompt_manager import PromptManager, Prompt, get_prompt_manager

# Create default prompt manager instance
prompt_manager = get_prompt_manager()

# Convenience functions
def get_prompt(agent: str, prompt_name: str = 'default') -> Prompt:
    """Get a prompt for an agent"""
    return prompt_manager.get_prompt(agent, prompt_name)


def format_prompt(agent: str, prompt_name: str = 'default', **kwargs) -> str:
    """Get and format a prompt"""
    return prompt_manager.format_prompt(agent, prompt_name, **kwargs)


def get_system_prompt(mode: str = 'default') -> str:
    """Get system prompt"""
    return prompt_manager.get_system_prompt(mode)


def reload_prompts() -> None:
    """Reload all prompts from disk"""
    prompt_manager.reload_prompts()


__all__ = [
    'PromptManager',
    'Prompt',
    'get_prompt_manager',
    'get_prompt',
    'format_prompt',
    'get_system_prompt',
    'reload_prompts'
]
