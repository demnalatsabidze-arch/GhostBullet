document.addEventListener('DOMContentLoaded', () => {
    fetchSites();
    // Poll for updates every 5 seconds
    setInterval(fetchSites, 5000);
});

// Modal UI logic
const modal = document.getElementById('create-modal');
const modalContent = document.getElementById('modal-content');

function openModal() {
    modal.classList.remove('hidden');
    // slight delay for animation
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        modalContent.classList.remove('scale-95');
    }, 10);
}

function closeModal() {
    modal.classList.add('opacity-0');
    modalContent.classList.add('scale-95');
    setTimeout(() => {
        modal.classList.add('hidden');
        document.getElementById('create-site-form').reset();
    }, 300);
}

const uploadModal = document.getElementById('upload-modal');
const uploadContent = document.getElementById('upload-content');

function closeUploadModal() {
    uploadModal.classList.add('opacity-0');
    uploadContent.classList.add('scale-95');
    setTimeout(() => {
        uploadModal.classList.add('hidden');
        document.getElementById('upload-site-form').reset();
        document.getElementById('file-name-display').textContent = 'Will overwrite existing files';
    }, 300);
}

function openUploadModal(siteId) {
    document.getElementById('upload-site-id').value = siteId;
    uploadModal.classList.remove('hidden');
    setTimeout(() => {
        uploadModal.classList.remove('opacity-0');
        uploadContent.classList.remove('scale-95');
    }, 10);
}

const filesModal = document.getElementById('files-modal');
const filesContent = document.getElementById('files-content');

function closeFilesModal() {
    filesModal.classList.add('opacity-0');
    filesContent.classList.add('scale-95');
    setTimeout(() => {
        filesModal.classList.add('hidden');
    }, 300);
}

function openFilesModal(siteId) {
    document.getElementById('manage-site-id').value = siteId;
    filesModal.classList.remove('hidden');
    setTimeout(() => {
        filesModal.classList.remove('opacity-0');
        filesContent.classList.remove('scale-95');
    }, 10);
    fetchFiles(siteId);
}

function toggleHostInputs() {
    const builtin = document.querySelector('input[name="host-type"][value="builtin"]').checked;
    const customInputs = document.getElementById('custom-host-inputs');
    if (builtin) {
        customInputs.classList.add('hidden');
        document.getElementById('site-host').required = false;
        document.getElementById('site-port').required = false;
    } else {
        customInputs.classList.remove('hidden');
        document.getElementById('site-host').required = true;
        document.getElementById('site-port').required = true;
    }
}

function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('block');
    });

    // Reset nav buttons
    const navButtons = document.querySelectorAll('nav button');
    navButtons.forEach(btn => {
        btn.classList.remove('border-cyan-400', 'text-cyan-400');
        btn.classList.add('border-transparent', 'text-zinc-500');
    });

    // Show active tab
    const activeContent = document.getElementById(`content-${tabId}`);
    if (activeContent) {
        activeContent.classList.remove('hidden');
        activeContent.classList.add('block');
    }

    // Highlight active button
    const activeBtn = document.getElementById(`tab-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.remove('border-transparent', 'text-zinc-500');
        activeBtn.classList.add('border-cyan-400', 'text-cyan-400');
    }
}

// Toast notification
function showToast(message) {
    const toast = document.getElementById('toast');
    document.getElementById('toast-msg').textContent = message;

    toast.classList.remove('translate-y-20', 'opacity-0');

    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3000);
}

// API Interactions

async function fetchSites() {
    try {
        const res = await fetch('/api/sites');
        const sites = await res.json();
        renderSites(sites);
    } catch (e) {
        console.error("Failed to fetch sites", e);
    }
}

document.getElementById('create-site-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const isBuiltin = document.querySelector('input[name="host-type"][value="builtin"]').checked;

    const data = {
        name: document.getElementById('site-name').value,
        is_builtin: isBuiltin,
        target_host: isBuiltin ? null : document.getElementById('site-host').value,
        target_port: isBuiltin ? null : document.getElementById('site-port').value,
        vanity_prefix: document.getElementById('site-vanity').value,
        description: document.getElementById('site-desc').value
    };

    try {
        const res = await fetch('/api/sites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            closeModal();
            showToast("Node initialized successfully");
            fetchSites();
        } else {
            const err = await res.json();
            showToast(`Error: ${err.error || 'Unknown error'}`);
        }
    } catch (e) {
        showToast("Network error creating site");
    }
});

document.getElementById('upload-site-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('file-upload');
    if (!fileInput.files.length) {
        showToast("Please select a .zip file");
        return;
    }

    const siteId = document.getElementById('upload-site-id').value;
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const btn = document.querySelector('#upload-site-form button[type="submit"] span');
        const origText = btn.innerHTML;
        btn.innerHTML = 'UPLOADING <i class="fa-solid fa-spinner fa-spin"></i>';

        const res = await fetch(`/api/sites/${siteId}/upload`, {
            method: 'POST',
            body: formData
        });

        btn.innerHTML = origText;

        if (res.ok) {
            closeUploadModal();
            showToast("Content uploaded & deployed successfully");
            fetchSites();
        } else {
            const err = await res.json();
            showToast(`Upload failed: ${err.error || 'Unknown error'}`);
        }
    } catch (e) {
        showToast("Network error uploading file");
    }
});

async function actionSite(id, action) {
    try {
        const res = await fetch(`/api/sites/${id}/${action}`, {
            method: 'POST'
        });
        if (res.ok) {
            fetchSites();
            showToast(`Action ${action} initiated`);
        }
    } catch (e) {
        showToast("Error performing action");
    }
}

async function deleteSite(id) {
    if (!confirm("Permenantly delete this node?")) return;
    try {
        const res = await fetch(`/api/sites/${id}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            fetchSites();
            showToast("Node deleted");
        }
    } catch (e) {
        showToast("Error deleting node");
    }
}

async function checkUpdates(id) {
    try {
        showToast("Scanning container packages...");
        const res = await fetch(`/api/sites/${id}/check-updates`, { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            // Delay toast slightly for visual effect
            setTimeout(() => {
                showToast(data.message || "Packages are up to date!");
            }, 1000);
        } else {
            showToast("Failed to check updates");
        }
    } catch (e) {
        showToast("Error checking updates");
    }
}

async function fetchFiles(siteId) {
    const tbody = document.getElementById('files-list-body');
    const loading = document.getElementById('files-loading');

    tbody.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const res = await fetch(`/api/sites/${siteId}/files`);
        const files = await res.json();

        loading.classList.add('hidden');

        if (files.error) {
            showToast("Error loading files: " + files.error);
            return;
        }

        if (files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="px-3 py-4 text-center text-zinc-600">Directory is empty</td></tr>';
            return;
        }

        files.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-3 py-2 text-zinc-300">${f.name}</td>
                <td class="px-3 py-2 text-right">${f.size}</td>
                <td class="px-3 py-2 text-right">
                    <button onclick="deleteFile('${siteId}', '${f.name}')" class="text-zinc-500 hover:text-rose-500 transition-colors">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        loading.classList.add('hidden');
        showToast("Error loading files");
    }
}

async function deleteFile(siteId, filename) {
    if (!confirm(`Permanently delete ${filename}?`)) return;
    try {
        const res = await fetch(`/api/sites/${siteId}/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            showToast("File deleted");
            fetchFiles(siteId);
        } else {
            showToast("Failed to delete file");
        }
    } catch (e) {
        showToast("Error deleting file");
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast("Onion address copied to clipboard");
    });
}

// Render Logic
const statusConfig = {
    'stopped': { icon: 'fa-circle', class: 'status-stopped', text: 'STOPPED' },
    'starting': { icon: 'fa-spinner fa-spin', class: 'status-starting', text: 'STARTING' },
    'generating_vanity': { icon: 'fa-microchip fa-fade', class: 'status-generating_vanity', text: 'COMPUTING VANITY' },
    'running': { icon: 'fa-bolt', class: 'status-running', text: 'ONLINE' },
    'error': { icon: 'fa-triangle-exclamation', class: 'status-error', text: 'ERROR' }
};

function renderSites(sites) {
    const container = document.getElementById('sites-container');
    const template = document.getElementById('site-card-template');

    container.innerHTML = '';

    if (sites.length === 0) {
        container.innerHTML = `
            <div class="col-span-full py-12 text-center text-zinc-600 font-mono text-sm border border-dashed border-zinc-800 rounded flex flex-col items-center justify-center gap-3">
                <i class="fa-solid fa-ghost text-4xl opacity-50 mb-2 text-zinc-700"></i>
                <div>NO ACTIVE NODES DETECTED</div>
                <div class="text-xs opacity-50">Initialize a new node to begin routing</div>
            </div>
        `;
        return;
    }

    sites.forEach(site => {
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.site-card');

        // Populate info
        clone.querySelector('.site-name').textContent = site.name;
        clone.querySelector('.target-info').innerHTML = `<i class="fa-solid fa-arrow-right-arrow-left text-zinc-600 mr-1"></i> ${site.target_host}:${site.target_port}`;

        // Status Badge
        const sConf = statusConfig[site.status] || statusConfig['error'];
        const badge = clone.querySelector('.status-badge');
        badge.className += ` ${sConf.class}`;
        badge.innerHTML = `<i class="fa-solid ${sConf.icon}"></i> ${sConf.text}`;

        // Onion Address
        const urlEl = clone.querySelector('.onion-url');
        const copyBtn = clone.querySelector('.copy-btn');
        if (site.onion_address) {
            urlEl.textContent = site.onion_address;
            urlEl.classList.remove('text-cyan-300');
            urlEl.classList.add('text-green-400');
            copyBtn.classList.remove('hidden');
            copyBtn.onclick = () => copyToClipboard(site.onion_address);
        } else if (site.status === 'generating_vanity') {
            urlEl.innerHTML = `<span class="animate-pulse text-fuchsia-400">Computing keys (prefix: ${site.vanity_prefix})...</span>`;
        } else if (site.is_deployed) {
            urlEl.innerHTML = `<span class="animate-pulse text-yellow-400">Waiting for Tor Manager...</span>`;
        }

        // Meta
        clone.querySelector('.vanity-val').textContent = site.vanity_prefix ? site.vanity_prefix : 'NONE';
        clone.querySelector('.vanity-val').className = site.vanity_prefix ? 'text-fuchsia-400 font-bold' : 'text-zinc-600';

        const date = new Date(site.created_at);
        clone.querySelector('.created-val').textContent = date.toLocaleDateString();

        // Buttons Logic
        const deployBtn = clone.querySelector('.deploy-btn');
        const uploadBtn = clone.querySelector('.upload-btn');
        const updateBtn = clone.querySelector('.update-btn');
        const manageBtn = clone.querySelector('.manage-btn');
        const checkPkgBtn = clone.querySelector('.check-pkg-btn');
        const stopBtn = clone.querySelector('.stop-btn');
        const regenBtn = clone.querySelector('.regen-btn');
        const deleteBtn = clone.querySelector('.delete-btn');

        if (site.is_deployed) {
            deployBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            regenBtn.classList.remove('hidden');

            if (site.is_builtin) {
                if (updateBtn) updateBtn.classList.remove('hidden');
                if (manageBtn) manageBtn.classList.remove('hidden');
                if (checkPkgBtn) checkPkgBtn.classList.remove('hidden');
                if (uploadBtn) uploadBtn.classList.add('hidden');
            }
        } else {
            deployBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
            regenBtn.classList.add('hidden');

            if (site.is_builtin && uploadBtn) {
                uploadBtn.classList.remove('hidden');
            }
            if (updateBtn) updateBtn.classList.add('hidden');
            if (manageBtn) manageBtn.classList.add('hidden');
            if (checkPkgBtn) checkPkgBtn.classList.add('hidden');
        }

        if (uploadBtn) uploadBtn.onclick = () => openUploadModal(site.id);
        if (updateBtn) updateBtn.onclick = () => openUploadModal(site.id);
        if (manageBtn) manageBtn.onclick = () => openFilesModal(site.id);
        if (checkPkgBtn) checkPkgBtn.onclick = () => checkUpdates(site.id);

        deployBtn.onclick = () => actionSite(site.id, 'deploy');
        stopBtn.onclick = () => actionSite(site.id, 'stop');
        regenBtn.onclick = () => actionSite(site.id, 'regenerate');
        deleteBtn.onclick = () => deleteSite(site.id);

        container.appendChild(clone);
    });
}
