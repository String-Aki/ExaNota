document.addEventListener('DOMContentLoaded', () => {
    const modeBtns = document.querySelectorAll('.mode-btn');
    const modeTitle = document.getElementById('modeTitle');
    const examSettings = document.getElementById('examSettings');
    const dictInput = document.getElementById('dictInput');
    const fileNameInput = document.getElementById('fileName');
    const generateBtn = document.getElementById('generateBtn');
    const clearBtn = document.getElementById('clearBtn');
    const templateTrigger = document.getElementById('templateTrigger');
    const templateFile = document.getElementById('templateFile');
    const templateStatus = document.getElementById('templateStatus');
    const editorOverlay = document.getElementById('editorOverlay');
    const statusMsg = document.getElementById('statusMsg');
    const statusTitle = document.getElementById('statusTitle');
    const statusDesc = document.getElementById('statusDesc');

    const closeStatus = document.getElementById('closeStatus');

    let currentMode = 'notes';
    let statusTimeout;

    // --- MODE SWITCHING ---
    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;
            
            modeTitle.textContent = currentMode === 'notes' ? 'Notes Scripter' : 'Exam Setter';
            examSettings.style.display = currentMode === 'exam' ? 'block' : 'none';
            
            if (dictInput.value) triggerParse();
        });
    });

    // --- TEMPLATE HANDLING ---
    templateTrigger.addEventListener('click', () => templateFile.click());
    templateFile.addEventListener('change', () => {
        if (templateFile.files.length > 0) {
            templateStatus.textContent = templateFile.files[0].name;
            templateStatus.style.color = '#818cf8';
        } else {
            templateStatus.textContent = 'Default Styles';
            templateStatus.style.color = '';
        }
    });

    // --- AUTO-PARSE TITLE ---
    let parseTimeout;
    dictInput.addEventListener('input', () => {
        clearTimeout(parseTimeout);
        parseTimeout = setTimeout(triggerParse, 800);
    });

    async function triggerParse() {
        const val = dictInput.value.trim();
        if (!val) return;

        editorOverlay.style.display = 'flex';
        try {
            const res = await fetch('/api/parse-title', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ python_dict: val })
            });
            if (res.ok) {
                const data = await res.json();
                fileNameInput.value = data.suggested_filename;
            }
        } catch (e) {
            console.error('Parse failed', e);
        } finally {
            editorOverlay.style.display = 'none';
        }
    }

    // --- GENERATION ---
    generateBtn.addEventListener('click', async () => {
        const pythonDict = dictInput.value.trim();
        const fileName = fileNameInput.value.trim();

        if (!pythonDict || !fileName) {
            showStatus('Missing Info', 'Please provide a dictionary and a file name.', 'error');
            return;
        }

        generateBtn.disabled = true;
        showStatus('Processing', 'Formatting your document...', 'success');

        const formData = new FormData();
        formData.append('mode', currentMode);
        formData.append('python_dict', pythonDict);
        formData.append('filename', fileName);
        formData.append('is_tamil', document.getElementById('tamilToggle').checked);
        formData.append('is_teacher_copy', document.getElementById('teacherToggle').checked);
        if (templateFile.files.length > 0) {
            formData.append('template', templateFile.files[0]);
        }

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = fileName.endsWith('.docx') ? fileName : fileName + '.docx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                showStatus('Success', `Generated ${a.download} successfully.`, 'success');
            } else {
                let errText = 'Unknown error';
                try {
                    const errJson = await res.json();
                    errText = errJson.detail;
                } catch(e) {
                    errText = await res.text();
                }
                showStatus('Generation Failed', errText, 'error');
            }
        } catch (e) {
            showStatus('Error', e.message, 'error');
        } finally {
            generateBtn.disabled = false;
        }
    });

    // --- CLEAR WORKSPACE ---
    clearBtn.addEventListener('click', () => {
        if (dictInput.value.trim() === '' || confirm('Are you sure you want to clear your work?')) {
            dictInput.value = '';
            fileNameInput.value = '';
            showStatus('Workspace Cleared', 'The editor has been reset.', 'success');
        }
    });

    // --- UI HELPERS ---
    closeStatus.addEventListener('click', () => {
        statusMsg.classList.add('hidden');
        clearTimeout(statusTimeout);
    });

    function showStatus(title, desc, type) {
        clearTimeout(statusTimeout);
        statusMsg.classList.remove('hidden', 'success', 'error');
        if (type) statusMsg.classList.add(type);
        
        statusTitle.textContent = title;
        statusDesc.textContent = desc;
        
        // Auto-hide unless it's a "Processing" state
        if (title !== 'Processing') {
            const delay = type === 'error' ? 8000 : 5000;
            statusTimeout = setTimeout(() => {
                statusMsg.classList.add('hidden');
            }, delay);
        }
    }
});
