import hljs from 'highlight.js';
import 'highlight.js/lib/common'; // Import common languages
import mermaid from 'mermaid';

// Initialize highlight.js theme
let themeLoaded = false;

/**
 * Load highlight.js theme dynamically
 */
async function loadHighlightTheme() {
  if (themeLoaded) return;

  try {
    // Remove any existing highlight.js style
    const existingStyle = document.querySelector('style[data-hljs-theme]');
    if (existingStyle) {
      existingStyle.remove();
    }

    // Import GitHub dark theme
    const cssModule = await import('highlight.js/styles/github-dark.css?inline');
    
    // Create and inject the style with higher specificity
    const style = document.createElement('style');
    style.textContent = `
      /* Highlight.js theme with proper specificity */
      ${cssModule.default}
      
      /* Enhanced syntax highlighting for dark theme */
      .code-block-container .hljs {
        background: transparent !important;
        color: #c9d1d9 !important;
      }
      
      .code-block-container .hljs-keyword { color: #ff7b72 !important; }
      .code-block-container .hljs-string { color: #a5d6ff !important; }
      .code-block-container .hljs-comment { color: #8b949e !important; }
      .code-block-container .hljs-number { color: #79c0ff !important; }
      .code-block-container .hljs-function { color: #d2a8ff !important; }
      .code-block-container .hljs-variable { color: #ffa657 !important; }
      .code-block-container .hljs-property { color: #79c0ff !important; }
      .code-block-container .hljs-title { color: #d2a8ff !important; }
      .code-block-container .hljs-attr { color: #79c0ff !important; }
      .code-block-container .hljs-built_in { color: #ffa657 !important; }
    `;
    style.setAttribute('data-hljs-theme', 'github-dark');
    document.head.appendChild(style);
    
    themeLoaded = true;
    console.log('Highlight.js theme loaded successfully');
  } catch (error) {
    console.warn('Failed to load highlight.js theme:', error);
    // Fallback: Add comprehensive highlighting styles
    const fallbackStyle = document.createElement('style');
    fallbackStyle.textContent = `
      .code-block-container .hljs { color: #c9d1d9 !important; background: transparent !important; }
      .code-block-container .hljs-keyword { color: #ff7b72 !important; }
      .code-block-container .hljs-string { color: #a5d6ff !important; }
      .code-block-container .hljs-comment { color: #8b949e !important; }
      .code-block-container .hljs-number { color: #79c0ff !important; }
      .code-block-container .hljs-function { color: #d2a8ff !important; }
      .code-block-container .hljs-variable { color: #ffa657 !important; }
      .code-block-container .hljs-property { color: #79c0ff !important; }
      .code-block-container .hljs-title { color: #d2a8ff !important; }
      .code-block-container .hljs-attr { color: #79c0ff !important; }
      .code-block-container .hljs-built_in { color: #ffa657 !important; }
      .code-block-container .hljs-literal { color: #79c0ff !important; }
      .code-block-container .hljs-type { color: #ffa657 !important; }
    `;
    fallbackStyle.setAttribute('data-hljs-theme', 'fallback');
    document.head.appendChild(fallbackStyle);
    themeLoaded = true;
    console.log('Fallback highlight.js theme loaded');
  }
}

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'monospace',
});

/**
 * HTML escape utility function
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Generate unique ID for mermaid diagrams
 */
function generateMermaidId(): string {
  return `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

/**
 * Render code block with syntax highlighting
 */
function renderCodeBlock(language: string, code: string): string {
  const cleanCode = code.trim();
  const formattedLanguage = language.toLowerCase();
  
  // Handle special cases
  if (formattedLanguage === 'mermaid') {
    const mermaidId = generateMermaidId();
    // Return a placeholder that will be processed later
    return `<div class="mermaid-diagram" data-mermaid-id="${mermaidId}" data-mermaid-code="${escapeHtml(cleanCode)}"></div>`;
  }
  
  if (formattedLanguage === '__html') {
    return `<div class="raw-html-block bg-slate-700/30 p-4 rounded border border-slate-600/30">${cleanCode}</div>`;
  }
  
  // Regular code block with syntax highlighting
  let highlightedCode = escapeHtml(cleanCode);
  let hlClass = '';
  
  console.log(`Attempting to highlight language: "${formattedLanguage}"`);
  console.log(`Available languages:`, hljs.listLanguages());
  
  try {
    const lang = hljs.getLanguage(formattedLanguage);
    console.log(`Language "${formattedLanguage}" detection result:`, lang);
    
    if (lang) {
      const result = hljs.highlight(cleanCode, { language: formattedLanguage });
      highlightedCode = result.value;
      hlClass = 'hljs';
      console.log(`Successfully highlighted ${formattedLanguage} code:`, result);
    } else {
      console.warn(`Language ${formattedLanguage} not supported by highlight.js. Available:`, hljs.listLanguages().slice(0, 10));
      // Try auto-detection as fallback
      try {
        const autoResult = hljs.highlightAuto(cleanCode);
        if (autoResult.language) {
          highlightedCode = autoResult.value;
          hlClass = 'hljs';
          console.log(`Auto-detected language: ${autoResult.language}`);
        }
      } catch (autoError) {
        console.warn('Auto-detection also failed:', autoError);
      }
    }
  } catch (error) {
    console.warn(`Failed to highlight ${formattedLanguage}:`, error);
  }
  
  const languageLabel = formattedLanguage || 'text';
  
  return `
    <div class="code-block-container bg-slate-700/30 rounded-lg border border-slate-600/30 my-4 overflow-hidden">
      <div class="code-block-header flex justify-between items-center px-3 py-2 bg-slate-800/50 border-b border-slate-600/30">
        <span class="text-xs font-mono text-slate-300">${languageLabel}</span>
        <button class="copy-btn text-slate-400 hover:text-slate-200 text-xs px-2 py-1 rounded hover:bg-slate-600/50 transition-colors" 
                data-copy-text="${escapeHtml(cleanCode).replace(/"/g, '&quot;')}"
                onclick="window.copyCodeBlock && window.copyCodeBlock(this)">
          Copy
        </button>
      </div>
      <pre class="p-4 overflow-x-auto text-sm bg-transparent"><code class="language-${formattedLanguage} ${hlClass}">${highlightedCode}</code></pre>
    </div>
  `;
}

/**
 * Process mermaid diagrams after DOM insertion
 */
async function processMermaidDiagrams() {
  const mermaidElements = document.querySelectorAll('.mermaid-diagram');
  
  for (const element of mermaidElements) {
    const mermaidId = element.getAttribute('data-mermaid-id');
    const mermaidCode = element.getAttribute('data-mermaid-code');
    
    if (mermaidId && mermaidCode) {
      try {
        // Create mermaid container
        const container = document.createElement('div');
        container.className = 'mermaid-container bg-slate-700/30 p-4 rounded-lg border border-slate-600/30 my-4 text-center';
        container.innerHTML = mermaidCode;
        
        // Render mermaid diagram
        const { svg } = await mermaid.render(mermaidId, mermaidCode);
        container.innerHTML = svg;
        
        // Replace placeholder with rendered diagram
        element.parentNode?.replaceChild(container, element);
      } catch (error) {
        console.warn('Failed to render mermaid diagram:', error);
        // Fallback to code block
        element.outerHTML = `<pre class="bg-slate-700/50 p-3 rounded text-sm overflow-x-auto border border-slate-600/30"><code>${escapeHtml(mermaidCode || '')}</code></pre>`;
      }
    }
  }
}

/**
 * Copy to clipboard functionality (injected globally)
 */
if (typeof window !== 'undefined') {
  (window as any).copyCodeBlock = async (button: HTMLElement) => {
    try {
      const text = button.getAttribute('data-copy-text') || '';
      const decodedText = text.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
      
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(decodedText);
      } else {
        // Fallback to traditional method
        const textArea = document.createElement('textarea');
        textArea.value = decodedText;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      
      const originalText = button.textContent;
      button.textContent = 'Copied!';
      button.classList.add('text-green-400');
      setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('text-green-400');
      }, 2000);
    } catch (error) {
      console.warn('Failed to copy to clipboard:', error);
      // Show error feedback
      const originalText = button.textContent;
      button.textContent = 'Failed';
      button.classList.add('text-red-400');
      setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('text-red-400');
      }, 2000);
    }
  };
}

/**
 * Improved markdown to HTML converter with highlight.js and mermaid support
 */
export async function markdownToHtml(md: string): Promise<string> {
  if (!md || typeof md !== 'string') {
    return '';
  }

  // Load highlight.js theme
  await loadHighlightTheme();

  // Store code blocks temporarily to avoid processing them
  const codeBlocks: string[] = [];
  const codeBlockPlaceholder = '___CODE_BLOCK___';
  
  // Store inline code temporarily
  const inlineCodes: string[] = [];
  const inlineCodePlaceholder = '___INLINE_CODE___';
  
  let result = md.trim();

  // 1. Extract and preserve code blocks first (to avoid processing markdown inside them)
  result = result.replace(/```(\w+)?\n?([\s\S]*?)```/gim, (_match, language, code) => {
    const lang = language || '';
    const renderedBlock = renderCodeBlock(lang, code);
    codeBlocks.push(renderedBlock);
    return `${codeBlockPlaceholder}${codeBlocks.length - 1}`;
  });

  // 2. Extract and preserve inline code
  result = result.replace(/`([^`\n]+)`/g, (_match, code) => {
    inlineCodes.push(`<code class="bg-slate-700/50 px-1 py-0.5 rounded text-sm border border-slate-600/30 font-mono">${escapeHtml(code)}</code>`);
    return `${inlineCodePlaceholder}${inlineCodes.length - 1}`;
  });

  // 3. Process headings (with proper boundary checking)
  result = result.replace(/^(#{1,6})\s+(.+)$/gim, (_match, hashes, content) => {
    const level = hashes.length;
    const classes = [
      '', // level 0 (unused)
      'text-xl font-bold mb-3 mt-4', // h1
      'text-lg font-semibold mb-2 mt-3', // h2  
      'text-base font-medium mb-2 mt-2', // h3
      'text-sm font-medium mb-1 mt-2', // h4
      'text-sm font-medium mb-1 mt-1', // h5
      'text-xs font-medium mb-1 mt-1', // h6
    ];
    return `<h${level} class="${classes[level] || classes[3]}">${escapeHtml(content.trim())}</h${level}>`;
  });

  // 4. Process images (before links to avoid conflicts)
  result = result.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_match, alt, url) => {
    return `<img src="${escapeHtml(url.trim())}" alt="${escapeHtml(alt)}" class="max-w-full h-auto rounded-lg shadow-sm my-2" loading="lazy" />`;
  });

  // 5. Process links
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, text, url) => {
    // Handle timestamps specially
    if (/^\d{2}:\d{2}:\d{2}$/.test(text)) {
      return `<span class="text-blue-400 font-mono text-sm">[${text}]</span>`;
    }
    return `<a href="${escapeHtml(url.trim())}" class="text-blue-400 hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`;
  });

  // 6. Process bold text (non-greedy matching)
  result = result.replace(/\*\*([^*\n]+?)\*\*/g, (_match, content) => {
    return `<strong>${escapeHtml(content)}</strong>`;
  });

  // 7. Process italic text (non-greedy matching, avoid conflict with bold)
  result = result.replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, (_match, content) => {
    return `<em>${escapeHtml(content)}</em>`;
  });

  // 8. Process strikethrough
  result = result.replace(/~~([^~\n]+?)~~/g, (_match, content) => {
    return `<del>${escapeHtml(content)}</del>`;
  });

  // 9. Process highlight
  result = result.replace(/==([^=\n]+?)==/g, (_match, content) => {
    return `<mark class="bg-yellow-200 px-1">${escapeHtml(content)}</mark>`;
  });

  // 10. Process blockquotes
  result = result.replace(/^>\s*(.+)$/gim, (_match, content) => {
    return `<blockquote class="border-l-4 border-blue-500/50 pl-4 italic text-slate-300 my-2">${escapeHtml(content.trim())}</blockquote>`;
  });

  // 11. Process task lists
  result = result.replace(/^(\s*)[-*+]\s+\[([x\s])\]\s+(.+)$/gim, (_match, indent, check, content) => {
    const checked = check.toLowerCase() === 'x' ? 'checked' : '';
    const indentClass = indent.length > 0 ? `ml-${Math.min(indent.length, 8)}` : '';
    return `<li class="flex items-center ${indentClass} my-1"><input type="checkbox" ${checked} disabled class="mr-2"> <span>${escapeHtml(content.trim())}</span></li>`;
  });

  // 12. Process regular lists
  result = result.replace(/^(\s*)[-*+]\s+(.+)$/gim, (_match, indent, content) => {
    const indentClass = indent.length > 0 ? `ml-${Math.min(indent.length * 4, 16)}` : 'ml-4';
    return `<li class="${indentClass} my-1">${escapeHtml(content.trim())}</li>`;
  });

  // 13. Process horizontal rules
  result = result.replace(/^[-*_]{3,}\s*$/gim, '<hr class="border-slate-600/30 my-4">');

  // 14. Process line breaks (preserve double line breaks as paragraphs)
  result = result.replace(/\n\n+/g, '</p><p>');
  result = result.replace(/\n/g, '<br>');

  // 15. Wrap in paragraph tags if content exists
  if (result.trim() && !result.startsWith('<')) {
    result = `<p>${result}</p>`;
  }

  // 16. Restore code blocks
  result = result.replace(new RegExp(`${codeBlockPlaceholder}(\\d+)`, 'g'), (_match, index) => {
    return codeBlocks[parseInt(index)] || '';
  });

  // 17. Restore inline code
  result = result.replace(new RegExp(`${inlineCodePlaceholder}(\\d+)`, 'g'), (_match, index) => {
    return inlineCodes[parseInt(index)] || '';
  });

  // 18. Clean up empty paragraphs and fix nested issues
  result = result.replace(/<p>\s*<\/p>/g, '');
  result = result.replace(/<p>\s*(<h[1-6])/g, '$1');
  result = result.replace(/(<\/h[1-6]>)\s*<\/p>/g, '$1');
  result = result.replace(/<p>\s*(<hr)/g, '$1');
  result = result.replace(/(<\/hr>)\s*<\/p>/g, '$1');

  return result;
}

/**
 * Process the rendered HTML to handle mermaid diagrams
 * Call this after the HTML is inserted into the DOM
 */
export async function processMarkdownContent(_container: HTMLElement) {
  await processMermaidDiagrams();
}
