// Name: Sync lead updates with MC Operations Frappe CRM

const {
    recordId,
    leadEmail,
    leadPhone,
    principalDebt,
    firstName,
    lastName,
} = input.config();

// Mandatory fields that should be excluded from the request if they don't have a value
// This prevents sending empty/null values for required fields that would cause validation errors
const mandatoryFields = ['first_name'];

/**
 * Returns a safe value for a given field, applying fallback logic.
 * - If the field is an array, returns the first element if present, otherwise returns the fallback.
 * - If the field is null or undefined, returns the fallback.
 * - Otherwise, returns the field value as is.
 *
 * @param {*} field - The field value to process.
 * @param {*} [fallback=null] - The fallback value to use if the field is empty or not present.
 * @returns {*} - The processed field value or fallback.
 */
let safeFieldValue = (field, fallback = null) => {
    if (Array.isArray(field)) {
        return field.length > 0 ? field[0] : fallback;
    }
    return field ?? fallback;
}

/**
 * Creates a request body for lead updates, filtering out mandatory fields that don't have values.
 * 
 * Mandatory fields are completely excluded from the request if they
 * don't have a value, rather than being sent as null/empty. This prevents validation errors
 * on the server side for required fields.
 * 
 * @param {Object} fieldData - Object containing the field values
 * @returns {Object} - Filtered request body object
 */
let createRequestBody = (fieldData) => {
    let requestBody = {};

    for (let [key, value] of Object.entries(fieldData)) {
        let processedValue = safeFieldValue(value);

        // For mandatory fields, only include them if they have a truthy value
        if (mandatoryFields.includes(key)) {
            if (!(processedValue && processedValue.trim && processedValue.trim() !== '')) {
                continue; // Skip adding the field if it's mandatory and has no value
            }
        }
        // For non-mandatory fields, or mandatory fields with value, include them
        requestBody[key] = processedValue;
    }

    return requestBody;
}

// Site Setup Admin (The action must be done as a specific user)
let userApiKey = 'your-api-key';
let userApiSecret = 'your-api-secret';

try {
    // Prepare field data for request body creation
    let fieldData = {
        email: leadEmail,
        mobile_no: leadPhone,
        // custom_principal_debt: principalDebt,
        first_name: firstName,
        last_name: lastName
    };

    let requestBody = JSON.stringify(createRequestBody(fieldData));

    let response = await fetch(`https://mc-operations.f.frappe.cloud/api/resource/CRM Lead/${recordId}`, {
        method: "PUT",
        headers: {
            "Authorization": `token ${userApiKey}:${userApiSecret}`,
            "Content-Type": "application/json"
        },
        body: requestBody
    });

    // Capture complete response details for debugging and/or output
    let requestTrace = JSON.stringify(
        {
            status: response.status,
            statusText: response.statusText,
            requestBody: requestBody,
            body: await response.text().catch(() => "<could not read body>")
        }
    )

    output.set("requestTrace", requestTrace);

    if (!response.ok) {
        throw new Error(`Request failed ${requestTrace}`);
    }
} catch (error) {
    // Re-throw the error to fail the automation step to include error details
    // Without this, Airtable would raise it's own error without any context or explanation
    throw new Error(error);
}
