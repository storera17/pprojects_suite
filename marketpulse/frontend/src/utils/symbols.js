export function titleCase(value) {
    return String(value).replace(/[-_]/g, " ")
    .replace(/\b\w/g, (m) => m
    .toUpperCase());
}
