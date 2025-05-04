/**
 * Utility functions for safely handling arrays that might be undefined or null
 */

/**
 * Safely maps over an array, returning an empty array if the input is null/undefined
 * or if an error occurs during the mapping process.
 * @param arr The array to map over
 * @param mapFn The mapping function
 * @returns The mapped array or an empty array if input is invalid or mapping fails
 */
export function safeMap<T, U>(arr: T[] | null | undefined, mapFn: (item: T, index: number) => U): U[] {
  if (!arr || !Array.isArray(arr)) {
    // Don't warn if it's just null or undefined, only if it's not an array but truthy
    if (arr) {
        console.warn('safeMap called with non-array:', arr);
    }
    return [];
  }
  try {
    // Attempt the map operation
    return arr.map(mapFn);
  } catch (error) {
    // Catch errors thrown by the mapFn callback
    console.error("Error occurred inside safeMap's mapping function:", error);
    console.error("safeMap: Array being processed when error occurred:", arr);
    // Optionally, try to find the specific item causing the error, though this might be complex/slow
    // arr.forEach((item, index) => { try { mapFn(item, index); } catch (e) { console.error(`safeMap: Error likely at index ${index}, item:`, item, e); } });
    return []; // Return empty array on error to prevent crashing
  }
}

/**
 * Ensures a value is an array, returning an empty array if the input is null or undefined
 * @param arr The potential array
 * @returns The array or an empty array if input is null/undefined
 */
export function ensureArray<T>(arr: T[] | null | undefined): T[] {
  if (!arr || !Array.isArray(arr)) {
    return [];
  }
  return arr;
}

/**
 * Safely gets an item from an array at the specified index
 * @param arr The array to get the item from
 * @param index The index of the item
 * @returns The item or undefined if the array is invalid or the index is out of bounds
 */
export function safeArrayItem<T>(arr: T[] | null | undefined, index: number): T | undefined {
  if (!arr || !Array.isArray(arr) || index < 0 || index >= arr.length) {
    return undefined;
  }
  return arr[index];
}
