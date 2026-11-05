/**
 * Shared UI & Search Utilities for Taiwan NHI Drug Regulations Web App
 * Used by both Desktop (public/app.js) and Mobile (public/mobile.js).
 */
window.NHIShared = (() => {
    const CLAUSE_HEADER_RE = /^[（\(](\d+)[）\)]\s*([^：:\n]{2,32}?)[：:](.*)$/;

    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function escapeRegExp(string) {
        return String(string).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function cleanTitleForDisplay(title) {
        if (!title) return '';
        return title
            .replace(/（[^）]*\d+[^）]*）/g, '')
            .replace(/\([^)]*\d+[^)]*\)/g, '')
            .trim();
    }

    function formatDatesForDisplay(dates) {
        if (!dates || dates.length === 0) return '未特別標註';
        if (dates.length <= 2) return dates.join(', ');
        return `${dates[0]} ... ${dates[dates.length - 1]} (共 ${dates.length} 次修訂)`;
    }

    function cleanSummaryText(text, maxLen = 360) {
        if (!text) return '';
        const cleaned = text.replace(/【給付與評估表格.*?】:\s*/g, '').replace(/\|/g, ' - ');
        return cleaned.length > maxLen ? cleaned.substring(0, maxLen) + '...' : cleaned;
    }

    function createHighlightRegex(highlightTarget) {
        if (!highlightTarget) return null;
        if (Array.isArray(highlightTarget)) {
            const patterns = highlightTarget
                .map(t => escapeHtml(String(t).trim()))
                .filter(t => t.length >= 2)
                .sort((a, b) => b.length - a.length)
                .map(t => {
                    const parts = t.split(/\s+/).filter(Boolean).map(p => escapeRegExp(p));
                    return parts.join('[\\s\\u3000]*');
                })
                .filter(Boolean);
            if (patterns.length === 0) return null;
            return new RegExp(`(${patterns.join('|')})`, 'gi');
        }
        const escaped = escapeHtml(String(highlightTarget).trim());
        const parts = escaped.split(/\s+/).filter(Boolean).map(p => escapeRegExp(p));
        if (parts.length === 0) return null;
        return new RegExp(`(${parts.join('[\\s\\u3000]*')})`, 'gi');
    }

    function buildTableHtml(rows, highlightSnippet = null) {
        if (!rows || !rows.length) return '';
        const regex = highlightSnippet ? createHighlightRegex(highlightSnippet) : null;
        const formatCell = (c) => {
            let s = escapeHtml(c);
            if (regex) {
                s = s.replace(regex, `<mark class="grounding-highlight">$1</mark>`);
            }
            return s;
        };

        let html = '<div class="table-responsive"><table class="clinical-table">';
        rows.forEach((rowStr, idx) => {
            const cells = rowStr.split('|').map(c => c.trim());
            if (idx === 0) {
                html += '<thead><tr>' + cells.map(c => `<th>${formatCell(c)}</th>`).join('') + '</tr></thead><tbody>';
            } else {
                html += '<tr>' + cells.map(c => `<td>${formatCell(c)}</td>`).join('') + '</tr>';
            }
        });
        html += '</tbody></table></div>';
        return html;
    }

    function renderFormattedText(container, text, highlightSnippet = null, anchorPrefix = 'clause-sec') {
        if (!container) return;
        if (!text) {
            container.innerHTML = '';
            return;
        }

        const lines = text.split('\n');
        const htmlParts = [];
        let inTable = false;
        let tableRows = [];
        const clauseNavItems = [];
        const regex = createHighlightRegex(highlightSnippet);
        const primaryTerm = Array.isArray(highlightSnippet) && highlightSnippet.length > 0
            ? highlightSnippet[0].toLowerCase()
            : null;

        lines.forEach((line, lineIdx) => {
            const trimmed = line.trim();
            if (trimmed.includes('|')) {
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                tableRows.push(trimmed);
            } else {
                if (inTable) {
                    inTable = false;
                    htmlParts.push(buildTableHtml(tableRows, highlightSnippet));
                    tableRows = [];
                }
                if (trimmed) {
                    const clauseMatch = trimmed.match(CLAUSE_HEADER_RE);
                    let safeLine = escapeHtml(trimmed);
                    if (regex) {
                        safeLine = safeLine.replace(regex, `<mark class="grounding-highlight">$1</mark>`);
                    }
                    if (clauseMatch) {
                        const cNum = clauseMatch[1];
                        const cTitle = clauseMatch[2].trim();
                        const anchorId = `${anchorPrefix}-${cNum}-${lineIdx}`;
                        const isMatched = Boolean(
                            (primaryTerm && cTitle.toLowerCase().includes(primaryTerm)) ||
                            (regex && cTitle.match(createHighlightRegex(highlightSnippet)))
                        );
                        clauseNavItems.push({ num: cNum, title: cTitle, anchorId, matched: isMatched });
                        htmlParts.push(`<div id="${anchorId}" class="clause-header ${isMatched ? 'clause-header-matched' : ''}">${safeLine}</div>`);
                    } else if (trimmed.startsWith('【')) {
                        htmlParts.push(`<h4 style="color:#38bdf8; margin-top:1rem;"><i class="fa-solid fa-table-list"></i> ${safeLine}</h4>`);
                    } else {
                        htmlParts.push(`<p style="margin-bottom:0.5rem;">${safeLine}</p>`);
                    }
                }
            }
        });

        if (inTable) {
            htmlParts.push(buildTableHtml(tableRows, highlightSnippet));
        }

        let navHtml = '';
        if (clauseNavItems.length >= 2) {
            const pillsHtml = clauseNavItems.map(item =>
                `<button type="button" class="clause-jump-pill ${item.matched ? 'matched' : ''}" data-target="${item.anchorId}">(${escapeHtml(item.num)}) ${escapeHtml(item.title)}</button>`
            ).join('');
            navHtml = `
                <div class="clause-jump-bar">
                    <span class="clause-jump-label"><i class="fa-solid fa-compass"></i> 條文段落快速跳轉 (點擊定位)：</span>
                    <div class="clause-jump-pills">${pillsHtml}</div>
                </div>
            `;
        }

        container.innerHTML = navHtml + htmlParts.join('');

        container.querySelectorAll('.clause-jump-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-target');
                const targetEl = document.getElementById(targetId);
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    targetEl.classList.add('clause-header-matched');
                }
            });
        });
    }

    function scrollToHighlight(container, fullText, highlightSnippet, occurrenceIdx = 0, anchorPrefix = 'clause-sec') {
        renderFormattedText(container, fullText, highlightSnippet, anchorPrefix);
        setTimeout(() => {
            const marks = container.querySelectorAll('.grounding-highlight');
            if (marks.length > 0) {
                const target = marks[Math.min(occurrenceIdx, marks.length - 1)];
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 60);
    }

    function resolveActiveHighlights(rawQuery, highlightTerms) {
        const trimmed = (rawQuery || '').trim();
        if (!trimmed) return [];
        if (Array.isArray(highlightTerms) && highlightTerms.length > 0) {
            return highlightTerms;
        }
        return trimmed.split(/[,，;；]+/).map(s => s.trim()).filter(s => s.length >= 2);
    }

    function autoScrollToFirstMatch(container, delayMs = 80) {
        setTimeout(() => {
            const targetEl = container.querySelector('.clause-header-matched') || container.querySelector('.grounding-highlight');
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, delayMs);
    }

    function populateModalDrugs(boxEl, listEl, reg) {
        if (!boxEl || !listEl) return;
        const ings = (reg.medications && reg.medications.ingredients) ? reg.medications.ingredients : [];
        const classes = (reg.medications && reg.medications.drug_classes) ? reg.medications.drug_classes : [];
        const combined = ings.length > 0 ? ings : classes;
        if (combined.length > 0) {
            listEl.textContent = combined.join(', ');
            boxEl.classList.remove('hidden');
        } else {
            boxEl.classList.add('hidden');
        }
    }

    function deduplicateBiomarkers(structuredBios) {
        const seenBios = new Set();
        const uniqueBios = [];
        (structuredBios || []).forEach(b => {
            const key = `${b.biomarker}${b.operator}${b.value}`;
            if (!seenBios.has(key)) {
                seenBios.add(key);
                uniqueBios.push(b);
            }
        });
        return uniqueBios;
    }

    function buildCardBadgesHtml(reg, { maxBios = 5, maxDrugs = 5, labClass = 'badge-lab', indClass = 'badge-indication' } = {}) {
        const structuredBios = reg.conditions_of_payment.structured_biomarkers || [];
        let labBadges = '';
        if (structuredBios.length > 0) {
            const uniqueBios = deduplicateBiomarkers(structuredBios);
            labBadges = uniqueBios.slice(0, maxBios).map(b => {
                const snippetText = b.source_grounding ? (b.source_grounding.snippet || b.source_grounding.matched_text || '') : '';
                const opStr = b.operator === 'status' ? '' : escapeHtml(b.operator);
                const valStr = escapeHtml(String(b.value));
                const unitStr = b.unit ? ' ' + escapeHtml(b.unit) : '';
                const titleAttr = snippetText ? ` title="點擊內文可定位原始依據: ${escapeHtml(snippetText)}"` : '';
                return `<span class="badge-biomarker"${titleAttr}><i class="fa-solid fa-vial-circle-check"></i> ${escapeHtml(b.biomarker)} ${opStr}${valStr}${unitStr}</span>`;
            }).join(' ');
        } else {
            const labs = reg.conditions_of_payment.laboratory_criteria || [];
            labBadges = labs.map(l => `<span class="${labClass}"><i class="fa-solid fa-flask"></i> ${escapeHtml(l)}</span>`).join(' ');
        }

        const priorAuthBadge = reg.conditions_of_payment.prior_authorization_required
            ? `<span class="badge-prior-auth" title="本藥品需事前審查核准"><i class="fa-solid fa-stamp"></i> 事前審查</span>`
            : '';

        const indications = reg.conditions_of_payment.indications || [];
        const indicationBadges = indications.map(ind => `<span class="${indClass}"><i class="fa-solid fa-notes-medical"></i> ${escapeHtml(ind)}</span>`).join(' ');

        const displayTitle = cleanTitleForDisplay(reg.section_title);
        const ingredients = (reg.medications && reg.medications.ingredients) ? reg.medications.ingredients : [];
        let drugBadges = '';
        if (ingredients.length > 0 && !/[A-Za-z]{4,}/.test(displayTitle)) {
            drugBadges = ingredients.slice(0, maxDrugs).map(ing =>
                `<span class="${labClass}" style="border-color:rgba(56,189,248,0.35); color:#38bdf8;"><i class="fa-solid fa-pills"></i> ${escapeHtml(ing)}</span>`
            ).join(' ');
        }

        return { displayTitle, priorAuthBadge, drugBadges, indicationBadges, labBadges };
    }

    function renderStructuredCriteria({ reg, criteriaSection, chipsContainer, priorAuthEl, fullTextContainer, anchorPrefix = 'clause-sec', maxRuleLen = 28 }) {
        if (!criteriaSection || !chipsContainer) return;
        chipsContainer.innerHTML = '';

        const fullText = reg.reference_annotations.full_text;
        const bios = reg.conditions_of_payment.structured_biomarkers || [];
        const steps = reg.conditions_of_payment.step_therapy || [];
        const stops = reg.conditions_of_payment.stopping_rules || [];
        const evals = reg.conditions_of_payment.evaluation_intervals || [];
        const priorAuth = reg.conditions_of_payment.prior_authorization_required;
        const priorAuthGrounding = reg.conditions_of_payment.prior_authorization_grounding;

        if (priorAuthEl) {
            if (priorAuth) {
                priorAuthEl.innerHTML = `<span class="badge-prior-auth" style="cursor:pointer;"><i class="fa-solid fa-stamp"></i> 需事前審查 (點擊定位)</span>`;
                const paMatch = priorAuthGrounding ? (priorAuthGrounding.snippet || priorAuthGrounding.matched_text || '') : '事前審查';
                if (paMatch) {
                    priorAuthEl.onclick = () => scrollToHighlight(fullTextContainer, fullText, paMatch, 0, anchorPrefix);
                }
            } else {
                priorAuthEl.innerHTML = '';
                priorAuthEl.onclick = null;
            }
        }

        const hasAnyStructured = bios.length > 0 || steps.length > 0 || stops.length > 0 || evals.length > 0 || priorAuth;
        if (!hasAnyStructured) {
            criteriaSection.classList.add('hidden');
            return;
        }
        criteriaSection.classList.remove('hidden');

        const activateChip = (chip) => {
            chipsContainer.querySelectorAll('.criteria-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
        };

        // Group identical biomarkers while preserving all occurrence snippets for cycling
        const groupedBios = [];
        const bioMap = new Map();
        bios.forEach((b) => {
            const key = `${b.biomarker}|${b.operator}|${b.value}|${b.unit || ''}`;
            const snippetText = b.source_grounding ? (b.source_grounding.snippet || b.source_grounding.matched_text || '') : '';
            if (!bioMap.has(key)) {
                const entry = { ...b, snippets: snippetText ? [snippetText] : [], clickIdx: 0 };
                bioMap.set(key, entry);
                groupedBios.push(entry);
            } else if (snippetText) {
                bioMap.get(key).snippets.push(snippetText);
            }
        });

        groupedBios.forEach((b) => {
            const chip = document.createElement('button');
            chip.className = 'criteria-chip';
            const countBadge = b.snippets.length > 1 ? ` <span style="opacity:0.75; font-size:0.72rem;">(×${b.snippets.length})</span>` : '';
            chip.title = b.snippets.length > 0 ? `點擊定位原文 (${b.snippets.length} 處): ${b.snippets[0]}` : '點擊定位原文';
            chip.innerHTML = `<i class="fa-solid fa-vial" style="color:#10b981;"></i> <strong>${escapeHtml(b.biomarker)}</strong> ${escapeHtml(b.operator === 'status' ? '' : b.operator)} ${escapeHtml(String(b.value))}${b.unit ? ' ' + escapeHtml(b.unit) : ''}${countBadge}`;
            chip.addEventListener('click', () => {
                activateChip(chip);
                if (b.snippets.length > 0) {
                    const idx = b.clickIdx % b.snippets.length;
                    const targetSnippet = b.snippets[idx];
                    let sameSnippetOcc = 0;
                    for (let i = 0; i < idx; i++) {
                        if (b.snippets[i] === targetSnippet) sameSnippetOcc++;
                    }
                    b.clickIdx++;
                    scrollToHighlight(fullTextContainer, fullText, targetSnippet, sameSnippetOcc, anchorPrefix);
                }
            });
            chipsContainer.appendChild(chip);
        });

        evals.forEach((ev) => {
            const chip = document.createElement('button');
            chip.className = 'criteria-chip';
            const evLabel = typeof ev === 'string' ? ev : (ev.schedule || ev.frequency || '');
            const evSnippet = typeof ev === 'string' ? ev : (ev.source_grounding ? (ev.source_grounding.snippet || ev.source_grounding.matched_text) : evLabel);
            chip.innerHTML = `<i class="fa-regular fa-clock" style="color:#38bdf8;"></i> 評估/續用: ${escapeHtml(evLabel)}`;
            chip.addEventListener('click', () => {
                activateChip(chip);
                if (evSnippet) scrollToHighlight(fullTextContainer, fullText, evSnippet, 0, anchorPrefix);
            });
            chipsContainer.appendChild(chip);
        });

        steps.slice(0, 3).forEach((st) => {
            const chip = document.createElement('button');
            chip.className = 'criteria-chip';
            const stLabel = typeof st === 'string' ? st : (st.rule || st.requirement || '');
            const stSnippet = typeof st === 'string' ? st : (st.source_grounding ? (st.source_grounding.snippet || st.source_grounding.matched_text) : stLabel);
            const shortRule = stLabel.length > maxRuleLen ? stLabel.substring(0, maxRuleLen) + '...' : stLabel;
            chip.innerHTML = `<i class="fa-solid fa-stairs" style="color:#f59e0b;"></i> 二線/轉換條件: ${escapeHtml(shortRule)}`;
            chip.addEventListener('click', () => {
                activateChip(chip);
                if (stSnippet) scrollToHighlight(fullTextContainer, fullText, stSnippet, 0, anchorPrefix);
            });
            chipsContainer.appendChild(chip);
        });

        stops.slice(0, 3).forEach((sp) => {
            const chip = document.createElement('button');
            chip.className = 'criteria-chip';
            const spLabel = typeof sp === 'string' ? sp : (sp.rule || sp.condition || '');
            const spSnippet = typeof sp === 'string' ? sp : (sp.source_grounding ? (sp.source_grounding.snippet || sp.source_grounding.matched_text) : spLabel);
            const shortRule = spLabel.length > maxRuleLen ? spLabel.substring(0, maxRuleLen) + '...' : spLabel;
            chip.innerHTML = `<i class="fa-solid fa-ban" style="color:#ef4444;"></i> 停藥/排除: ${escapeHtml(shortRule)}`;
            chip.addEventListener('click', () => {
                activateChip(chip);
                if (spSnippet) scrollToHighlight(fullTextContainer, fullText, spSnippet, 0, anchorPrefix);
            });
            chipsContainer.appendChild(chip);
        });
    }

    async function fetchSearch({ q = '', chapter = '', lab = '', limit = 6, offset = 0, signal = undefined }) {
        const params = new URLSearchParams({
            q,
            chapter,
            lab,
            limit: String(limit),
            offset: String(offset),
        });
        const res = await fetch(`/api/search?${params.toString()}`, signal ? { signal } : undefined);
        return res.json();
    }

    async function submitUpload({ file, password, statusEl, onSuccess }) {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('password', password || '');

        statusEl.innerHTML = '<span style="color:#38bdf8;"><i class="fa-solid fa-spinner fa-spin"></i> 正在驗證密碼並解析檔案...</span>';
        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                statusEl.innerHTML = `<span style="color:#4ade80;"><i class="fa-solid fa-circle-check"></i> ${escapeHtml(data.message)} (${data.records_count} 筆規範已更新)</span>`;
                if (onSuccess) setTimeout(onSuccess, 1500);
            } else {
                statusEl.innerHTML = `<span style="color:#f43f5e;"><i class="fa-solid fa-triangle-exclamation"></i> 錯誤：${escapeHtml(data.message)}</span>`;
            }
        } catch (err) {
            statusEl.innerHTML = `<span style="color:#f43f5e;"><i class="fa-solid fa-triangle-exclamation"></i> 上傳失敗：${escapeHtml(err.message)}</span>`;
        }
    }

    return {
        escapeHtml,
        escapeRegExp,
        cleanTitleForDisplay,
        formatDatesForDisplay,
        cleanSummaryText,
        createHighlightRegex,
        buildTableHtml,
        renderFormattedText,
        scrollToHighlight,
        resolveActiveHighlights,
        autoScrollToFirstMatch,
        populateModalDrugs,
        deduplicateBiomarkers,
        buildCardBadgesHtml,
        renderStructuredCriteria,
        fetchSearch,
        submitUpload,
    };
})();
