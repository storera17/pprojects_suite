export function asArraty(value) {
    return Array.isArray(value) ? value : [value];
}

export function asObject(value) {
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}