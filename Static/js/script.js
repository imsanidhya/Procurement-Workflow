
/* =========================================================
   PROCUREMENT WORKFLOW - MAIN JAVASCRIPT
========================================================= */


/* =========================================================
   APPROVER LEVEL COUNTER
========================================================= */

let approverLevel = 1;


/* =========================================================
   ATTACHMENT STATE
========================================================= */

let selectedAttachmentFiles = [];


/* =========================================================
   DOM READY
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    initializeUserDropdown();

    initializeApproverCounter();

    initializeFormValidation();

    initializeAttachmentPreview();

    initializeImagePreviewModal();

    initializeExistingRemoveButtons();

});


/* =========================================================
   USER PROFILE DROPDOWN
========================================================= */

function initializeUserDropdown() {

    const userButton =
        document.getElementById("userProfileButton");

    const userDropdown =
        document.getElementById("userDropdown");


    if (!userButton || !userDropdown) {
        return;
    }


    userButton.addEventListener("click", function (event) {

        event.stopPropagation();

        const isOpen =
            userDropdown.style.display === "block";


        if (isOpen) {

            closeUserDropdown();

        } else {

            openUserDropdown();

        }

    });


    document.addEventListener("click", function (event) {

        if (
            !userDropdown.contains(event.target) &&
            !userButton.contains(event.target)
        ) {

            closeUserDropdown();

        }

    });


    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape") {

            closeUserDropdown();

        }

    });

}


/* =========================================================
   OPEN USER DROPDOWN
========================================================= */

function openUserDropdown() {

    const userDropdown =
        document.getElementById("userDropdown");

    const userButton =
        document.getElementById("userProfileButton");


    if (!userDropdown || !userButton) {
        return;
    }


    userDropdown.style.display = "block";

    userButton.classList.add("show");

}


/* =========================================================
   CLOSE USER DROPDOWN
========================================================= */

function closeUserDropdown() {

    const userDropdown =
        document.getElementById("userDropdown");

    const userButton =
        document.getElementById("userProfileButton");


    if (!userDropdown || !userButton) {
        return;
    }


    userDropdown.style.display = "none";

    userButton.classList.remove("show");

}


/* =========================================================
   APPROVER COUNTER INITIALIZATION
========================================================= */

function initializeApproverCounter() {

    const rows =
        document.querySelectorAll(".approver-row");


    if (rows.length > 0) {

        approverLevel = rows.length;

        updateApprovalLevels();

    }

}


/* =========================================================
   ADD APPROVER
========================================================= */

function addApprover() {

    const container =
        document.getElementById("approverContainer");


    if (!container) {
        return;
    }


    approverLevel++;


    const newRow =
        document.createElement("div");


    newRow.className =
        "approver-row mt-3";


    newRow.innerHTML = `

        <div class="row align-items-center">

            <div class="col-md-1 text-center mb-3 mb-md-0">

                <span class="level-badge">
                    ${approverLevel}
                </span>

            </div>


            <div class="col-md-4 mb-3 mb-md-0">

                <label class="form-label mb-1">
                    Approval Level
                </label>

                <input
                    type="text"
                    class="form-control level-input"
                    value="Level ${approverLevel}"
                    readonly
                >

            </div>


            <div class="col-md-6 mb-3 mb-md-0">

                <label class="form-label mb-1">

                    Organization Email

                    <span class="required">*</span>

                </label>

                <input
                    type="email"
                    class="form-control"
                    name="approvers[]"
                    placeholder="approver@company.com"
                    required
                >

            </div>


            <div class="col-md-1 text-center">

                <button
                    type="button"
                    class="btn btn-outline-danger btn-sm remove-approver"
                    title="Remove Approval Level"
                >

                    <i class="bi bi-trash"></i>

                </button>

            </div>

        </div>

    `;


    container.appendChild(newRow);


    const removeButton =
        newRow.querySelector(".remove-approver");


    if (removeButton) {

        removeButton.addEventListener(
            "click",
            function () {

                removeApprover(removeButton);

            }
        );

    }


    updateApprovalLevels();

}


/* =========================================================
   REMOVE APPROVER
========================================================= */

function removeApprover(button) {

    const row =
        button.closest(".approver-row");


    if (!row) {
        return;
    }


    const rows =
        document.querySelectorAll(".approver-row");


    if (rows.length <= 1) {

        showMessage(
            "At least one approval level is required.",
            "warning"
        );

        return;
    }


    row.remove();

    updateApprovalLevels();

}


/* =========================================================
   UPDATE APPROVAL LEVELS
========================================================= */

function updateApprovalLevels() {

    const rows =
        document.querySelectorAll(".approver-row");


    rows.forEach(function (row, index) {

        const level =
            index + 1;


        const badge =
            row.querySelector(".level-badge");


        if (badge) {

            badge.textContent =
                level;

        }


        const levelInput =
            row.querySelector(".level-input");


        if (levelInput) {

            levelInput.value =
                `Level ${level}`;

        }

    });


    approverLevel =
        rows.length;

}


/* =========================================================
   FORM VALIDATION
========================================================= */

function initializeFormValidation() {

    const form =
        document.getElementById("requestForm");


    if (!form) {
        return;
    }


    /* =====================================================
       SAVE AS DRAFT

       IMPORTANT:
       Save as Draft is completely separate from the
       normal form validation.

       It does NOT call:
           form.checkValidity()

       It does NOT call:
           form.reportValidity()

       It does NOT use fetch()

       It directly submits the form to Flask.
    ===================================================== */

    const draftButton =
        document.getElementById("saveDraftButton");


    if (draftButton) {

        draftButton.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                event.stopPropagation();

                saveDraft();

            }
        );

    }
/* =====================================================
   SUBMIT EXISTING DRAFT
===================================================== */

const submitButton =
    document.getElementById("submitRequestButton");


if (submitButton) {

    submitButton.addEventListener(
        "click",
        function () {

            const isDraft =
                form.dataset.draft === "true";

            const requestNumber =
                form.dataset.requestNumber;


            /*
             * Existing draft:
             * Submit through /submit-draft/<request_number>
             */

            if (
                isDraft &&
                requestNumber
            ) {

                form.action =
                    `/submit-draft/${encodeURIComponent(requestNumber)}`;

            }

        }
    );

}

    /* =====================================================
       NORMAL FORM SUBMISSION

       Submit Request still validates all fields.
    ===================================================== */

    form.addEventListener(
        "submit",
        function (event) {

            /*
             * Save Draft uses form.submit(), so it never
             * reaches this event handler.
             *
             * This validation is therefore only for
             * normal Submit Request.
             */

            if (!form.checkValidity()) {

                event.preventDefault();

                event.stopPropagation();

                form.classList.add(
                    "was-validated"
                );

                return;

            }

        }
    );

}


/* =========================================================
   ATTACHMENT PREVIEW INITIALIZATION
========================================================= */

function initializeAttachmentPreview() {

    const input =
        document.getElementById("attachmentInput");


    if (!input) {
        return;
    }


    input.addEventListener(
        "change",
        handleAttachmentSelection
    );

}


/* =========================================================
   HANDLE ATTACHMENT SELECTION
========================================================= */

function handleAttachmentSelection(event) {

    const input =
        event.target;


    if (!input.files) {
        return;
    }


    selectedAttachmentFiles =
        Array.from(input.files);


    renderAttachmentPreviews();

}


/* =========================================================
   RENDER ATTACHMENT PREVIEWS
========================================================= */

function renderAttachmentPreviews() {

    const container =
        document.getElementById(
            "attachmentPreview"
        );


    const grid =
        document.getElementById(
            "attachmentPreviewGrid"
        );


    const count =
        document.getElementById(
            "attachmentCount"
        );


    if (!container || !grid) {
        return;
    }


    grid.innerHTML = "";


    if (
        selectedAttachmentFiles.length === 0
    ) {

        container.classList.remove("show");


        if (count) {

            count.textContent = "0";

        }


        return;

    }


    container.classList.add("show");


    if (count) {

        count.textContent =
            selectedAttachmentFiles.length;

    }


    selectedAttachmentFiles.forEach(
        function (file, index) {

            const card =
                createAttachmentPreviewCard(
                    file,
                    index
                );


            grid.appendChild(card);

        }
    );

}


/* =========================================================
   CREATE ATTACHMENT PREVIEW CARD
========================================================= */

function createAttachmentPreviewCard(
    file,
    index
) {

    const card =
        document.createElement("div");


    card.className =
        "attachment-preview-item";


    const isImage =
        file.type &&
        file.type.startsWith("image/");


    /* =====================================================
       IMAGE FILE
    ===================================================== */

    if (isImage) {

        const image =
            document.createElement("img");


        image.className =
            "attachment-preview-image";


        image.alt =
            file.name;


        image.title =
            "Click to view full size";


        const objectUrl =
            URL.createObjectURL(file);


        image.src =
            objectUrl;


        image.addEventListener(
            "click",
            function () {

                openImagePreview(
                    objectUrl,
                    file.name
                );

            }
        );


        card.appendChild(image);


        const zoomHint =
            document.createElement("div");


        zoomHint.className =
            "attachment-preview-zoom-hint";


        zoomHint.innerHTML =
            '<i class="bi bi-zoom-in"></i>';


        card.appendChild(zoomHint);

    }


    /* =====================================================
       NON-IMAGE FILE
    ===================================================== */

    else {

        const filePreview =
            document.createElement("div");


        filePreview.className =
            "attachment-file-preview";


        const extension =
            getFileExtension(file.name);


        if (extension === "pdf") {

            filePreview.classList.add("pdf");

        }

        else if (
            extension === "doc" ||
            extension === "docx"
        ) {

            filePreview.classList.add("word");

        }

        else if (
            extension === "xls" ||
            extension === "xlsx" ||
            extension === "csv"
        ) {

            filePreview.classList.add("excel");

        }

        else if (
            extension === "zip"
        ) {

            filePreview.classList.add("archive");

        }


        filePreview.innerHTML =
            getFileIcon(file.name);


        card.appendChild(filePreview);

    }


    /* =====================================================
       FILE NAME
    ===================================================== */

    const fileName =
        document.createElement("div");


    fileName.className =
        "attachment-preview-filename";


    fileName.textContent =
        file.name;


    fileName.title =
        `${file.name} (${formatFileSize(file.size)})`;


    card.appendChild(fileName);


    /* =====================================================
       REMOVE BUTTON
    ===================================================== */

    const removeButton =
        document.createElement("button");


    removeButton.type =
        "button";


    removeButton.className =
        "attachment-preview-remove";


    removeButton.title =
        "Remove file";


    removeButton.setAttribute(
        "aria-label",
        `Remove ${file.name}`
    );


    removeButton.innerHTML =
        '<i class="bi bi-x-lg"></i>';


    removeButton.addEventListener(
        "click",
        function (event) {

            event.stopPropagation();

            removeAttachment(index);

        }
    );


    card.appendChild(removeButton);


    return card;

}


/* =========================================================
   GET FILE EXTENSION
========================================================= */

function getFileExtension(filename) {

    return filename
        .split(".")
        .pop()
        .toLowerCase();

}


/* =========================================================
   REMOVE ATTACHMENT
========================================================= */

function removeAttachment(index) {

    if (
        index < 0 ||
        index >= selectedAttachmentFiles.length
    ) {
        return;
    }


    selectedAttachmentFiles.splice(
        index,
        1
    );


    updateFileInput();

    renderAttachmentPreviews();

}


/* =========================================================
   UPDATE ACTUAL FILE INPUT
========================================================= */

function updateFileInput() {

    const input =
        document.getElementById(
            "attachmentInput"
        );


    if (!input) {
        return;
    }


    const dataTransfer =
        new DataTransfer();


    selectedAttachmentFiles.forEach(
        function (file) {

            dataTransfer.items.add(file);

        }
    );


    input.files =
        dataTransfer.files;

}


/* =========================================================
   FILE ICON
========================================================= */

function getFileIcon(filename) {

    const extension =
        getFileExtension(filename);


    if (extension === "pdf") {

        return `
            <i class="bi bi-file-earmark-pdf"></i>
        `;

    }


    if (
        extension === "doc" ||
        extension === "docx"
    ) {

        return `
            <i class="bi bi-file-earmark-word"></i>
        `;

    }


    if (
        extension === "xls" ||
        extension === "xlsx" ||
        extension === "csv"
    ) {

        return `
            <i class="bi bi-file-earmark-spreadsheet"></i>
        `;

    }


    if (
        extension === "zip"
    ) {

        return `
            <i class="bi bi-file-earmark-zip"></i>
        `;

    }


    if (
        extension === "txt"
    ) {

        return `
            <i class="bi bi-file-earmark-text"></i>
        `;

    }


    return `
        <i class="bi bi-file-earmark"></i>
    `;

}


/* =========================================================
   FILE SIZE FORMATTER
========================================================= */

function formatFileSize(bytes) {

    if (bytes === 0) {
        return "0 Bytes";
    }


    const sizes = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];


    const i =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );


    return (
        parseFloat(
            (
                bytes /
                Math.pow(1024, i)
            ).toFixed(2)
        )
        +
        " "
        +
        sizes[i]
    );

}


/* =========================================================
   IMAGE PREVIEW MODAL
========================================================= */

function initializeImagePreviewModal() {

    const closeButton =
        document.getElementById(
            "closeImagePreview"
        );


    const backdrop =
        document.getElementById(
            "imagePreviewBackdrop"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeImagePreview
        );

    }


    if (backdrop) {

        backdrop.addEventListener(
            "click",
            closeImagePreview
        );

    }


    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Escape") {

                closeImagePreview();

            }

        }
    );

}


/* =========================================================
   OPEN FULL IMAGE PREVIEW
========================================================= */

function openImagePreview(
    imageUrl,
    fileName
) {

    const modal =
        document.getElementById(
            "imagePreviewModal"
        );


    const image =
        document.getElementById(
            "fullPreviewImage"
        );


    const name =
        document.getElementById(
            "fullPreviewFileName"
        );


    if (!modal || !image) {
        return;
    }


    image.src =
        imageUrl;


    if (name) {

        name.textContent =
            fileName;

    }


    modal.classList.add("show");


    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "preview-modal-open"
    );

}


/* =========================================================
   CLOSE FULL IMAGE PREVIEW
========================================================= */

function closeImagePreview() {

    const modal =
        document.getElementById(
            "imagePreviewModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove("show");


    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "preview-modal-open"
    );

}


/* =========================================================
   SAVE AS DRAFT
========================================================= */

function saveDraft() {

    const form =
        document.getElementById("requestForm");


    if (!form) {

        alert("Request form not found.");

        return;
    }


    const draftButton =
        document.getElementById(
            "saveDraftButton"
        );


    if (!draftButton) {

        alert("Save as Draft button not found.");

        return;
    }


    /*
       Prevent duplicate clicks.
    */

    if (
        draftButton.dataset.saving === "true"
    ) {

        return;
    }


    draftButton.dataset.saving = "true";


    console.log(
        "SAVE DRAFT BUTTON CLICKED"
    );


    /*
       =====================================================
       CRITICAL DRAFT BEHAVIOR
       =====================================================

       Save as Draft must NOT require ANY field.

       We therefore remove the required attribute from
       every field for this submission only.

       This includes:

       - Requester Name
       - Requester Email
       - Requirement Description
       - Business Requirement
       - Approver Email
       - Declaration
       - Any future required field
    */

    const requiredFields =
        form.querySelectorAll(
            "[required]"
        );


    requiredFields.forEach(
        function (field) {

            field.dataset.wasRequired =
                "true";

            field.removeAttribute(
                "required"
            );

        }
    );


    /*
       Remove any previous validation styling.
    */

    form.classList.remove(
        "was-validated"
    );


    form.querySelectorAll(
        ".is-invalid"
    ).forEach(
        function (field) {

            field.classList.remove(
                "is-invalid"
            );

        }
    );


    /*
       =====================================================
       SET ACTION = DRAFT
       =====================================================
    */

    let actionInput =
        form.querySelector(
            'input[name="action"]'
        );


    /*
       Remove an existing action input if there
       is one, because we want exactly one action=draft.
    */

    if (actionInput) {

        actionInput.remove();

    }


    actionInput =
        document.createElement(
            "input"
        );


    actionInput.type =
        "hidden";

    actionInput.name =
        "action";

    actionInput.value =
        "draft";


    form.appendChild(
        actionInput
    );


    /*
       =====================================================
       CHANGE BUTTON STATE
       =====================================================
    */

    draftButton.disabled =
        true;


    draftButton.innerHTML =
        '<i class="bi bi-hourglass-split me-1"></i> Saving...';


    /*
       =====================================================
       DIRECT FORM SUBMISSION
       =====================================================

       DO NOT use:

           fetch()

       DO NOT use:

           form.requestSubmit()

       DO NOT use:

           form.checkValidity()

       DO NOT use:

           form.reportValidity()

       HTMLFormElement.submit() sends the form directly
       to Flask and bypasses the normal submit event
       and validation handler.
    */

    try {

        HTMLFormElement.prototype.submit.call(
            form
        );

    }

    catch (error) {

        console.error(
            "Draft submission error:",
            error
        );


        /*
           Restore required attributes if something
           goes wrong before navigation.
        */

        requiredFields.forEach(
            function (field) {

                if (
                    field.dataset.wasRequired ===
                    "true"
                ) {

                    field.setAttribute(
                        "required",
                        ""
                    );

                }

            }
        );


        delete draftButton.dataset.saving;

        draftButton.disabled =
            false;


        draftButton.innerHTML =
            '<i class="bi bi-save me-1"></i> Save as Draft';


        showMessage(
            "Unable to submit the draft. Please try again.",
            "danger"
        );

    }

}


/* =========================================================
   FLASH MESSAGE HELPER
========================================================= */

function showMessage(
    message,
    type = "info"
) {

    const existingAlert =
        document.querySelector(
            ".js-alert"
        );


    if (existingAlert) {

        existingAlert.remove();

    }


    const alert =
        document.createElement("div");


    alert.className =
        `alert alert-${type} alert-dismissible fade show js-alert`;


    alert.setAttribute(
        "role",
        "alert"
    );


    alert.innerHTML = `

        ${escapeHtml(message)}

        <button
            type="button"
            class="btn-close"
            aria-label="Close"
        ></button>

    `;


    const form =
        document.getElementById(
            "requestForm"
        );


    if (form) {

        form.parentNode.insertBefore(
            alert,
            form
        );

    }


    const closeButton =
        alert.querySelector(
            ".btn-close"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            function () {

                alert.remove();

            }
        );

    }


    setTimeout(
        function () {

            if (alert) {

                alert.remove();

            }

        },
        5000
    );

}


/* =========================================================
   HTML ESCAPE HELPER
========================================================= */

function escapeHtml(value) {

    const div =
        document.createElement("div");


    div.textContent =
        value;


    return div.innerHTML;

}


/* =========================================================
   INITIALIZE EXISTING REMOVE BUTTONS
========================================================= */

function initializeExistingRemoveButtons() {

    const removeButtons =
        document.querySelectorAll(
            ".remove-approver"
        );


    removeButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    removeApprover(button);

                }
            );

        }
    );

}
