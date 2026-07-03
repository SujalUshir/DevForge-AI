import pytest
from pathlib import Path

from prompts.manager import PromptLoader, PromptSecurityError, PromptNotFoundError


def test_prompt_loader_success():
    """
    Test that PromptLoader resolves and reads existing markdown files successfully.
    """
    loader = PromptLoader()
    
    # Check loading ceo prompt
    content = loader.load_prompt("ceo.md")
    assert "# CEO Agent System Prompt" in content
    
    # Check cache hit on secondary load
    cached_content = loader.load_prompt("ceo")  # without extension
    assert cached_content == content


def test_prompt_loader_missing_file():
    """
    Test that PromptLoader throws a PromptNotFoundError for non-existent files.
    """
    loader = PromptLoader()
    with pytest.raises(PromptNotFoundError):
        loader.load_prompt("non_existent_role.md")


def test_prompt_loader_path_traversal_prevention():
    """
    Test that PromptLoader blocks directory traversal attempts using PromptSecurityError.
    """
    loader = PromptLoader()
    with pytest.raises(PromptSecurityError):
        # Attempt traversal outside backend/prompts/ folder
        loader.load_prompt("../main.py")
        
    with pytest.raises(PromptSecurityError):
        loader.load_prompt("..\\..\\README.md")
