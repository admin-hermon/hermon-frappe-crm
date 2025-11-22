// Airtable → Frappe CRM Lead upsert automation
// When a lead changes in Airtable, this script upserts (creates or updates) the CRM Lead via API.
const USER_API_KEY = 'your-api-key';
const USER_API_SECRET = 'your-api-secret';
const API_BASE_URL = 'https://site.f.frappe.cloud/api';
const MANDATORY_FIELDS = ['first_name'];

let normalizeFieldValue = (field, fallback = null) => {
    if (Array.isArray(field)) {
        return field.length > 0 ? field[0] : fallback;
    }

    return field ?? fallback;
}

let validateRequestData = (requestData) => {
    for (let field of MANDATORY_FIELDS) {
        if (
            !(field in requestData) ||
            requestData[field] === undefined ||
            requestData[field] === null ||
            (typeof requestData[field] === 'string' && requestData[field].trim() === '')
        ) {
            return false;
        }
    }

    return true;
}

let main = async () => {
    const {
        recordId,
        leadEmail,
        leadPhone,
        firstName,
        lastName,
        // principalDebt,
    } = input.config();

    let requestData = {
        first_name: normalizeFieldValue(firstName),
        last_name: normalizeFieldValue(lastName),
        email: normalizeFieldValue(leadEmail),
        mobile_no: normalizeFieldValue(leadPhone),
        // custom_principal_debt: normalizeFieldValue(principalDebt),
    }

    let requestDataValid = validateRequestData(requestData);

    if (!requestDataValid) {
        console.warn(`Request data ${JSON.stringify(requestData)} is not valid, skipping sync`);
        return;
    }

    console.info(`Syncing lead ${recordId} with request data ${JSON.stringify(requestData)}`);

    let updateResponse = await fetch(`${API_BASE_URL}/resource/CRM Lead/${recordId}`, {
        method: "PUT",
        headers: {
            "Authorization": `token ${USER_API_KEY}:${USER_API_SECRET}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
    });

    // 200 - 299 https://developer.mozilla.org/en-US/docs/Web/API/Response/ok
    if (updateResponse.ok) {
        console.info(`Lead ${recordId} updated successfully`);
        return;
    }

    if (updateResponse.status === 404) {
        console.info(`Lead ${recordId} not found, creating new lead`);

        let createResponse = await fetch(`${API_BASE_URL}/resource/CRM Lead`, {
            method: "POST",
            headers: {
                "Authorization": `token ${USER_API_KEY}:${USER_API_SECRET}`,
                "Content-Type": "application/json"
            },
            // Using airtable recordId as the name of the lead to maintain consistent identifiers between the systems
            body: JSON.stringify({ ...requestData, name: recordId })
        });

        if (createResponse.ok) {
            console.info(`Lead ${recordId} created successfully`);
            return;
        }

        throw new Error(`Failed to create lead ${recordId}: ${createResponse.status} ${await createResponse.text().catch(() => "<could not read body>")}`);
    }

    // Everything that's not 200 - 299 or 404 is considered an error
    throw new Error(`Failed to update lead ${recordId}: ${updateResponse.status} ${await updateResponse.text().catch(() => "<could not read body>")}`);
}

// This pattern is used to allow for early returns and make the main logic easier to focus on
main();
