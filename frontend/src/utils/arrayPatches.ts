/**
 * This file contains patches for native array methods to make them safe against undefined/null values.
 * It should be imported early in the application to ensure all array methods are patched.
 */

// Store the original Array.prototype.map method
const originalArrayMap = Array.prototype.map;

// Override the native map method to handle undefined/null arrays
Array.prototype.map = function<T, U>(
  this: T[] | null | undefined,
  callbackfn: (value: T, index: number, array: T[]) => U,
  thisArg?: any
): U[] {
  // If this is null or undefined, return an empty array
  if (this === null || this === undefined) {
    console.warn('Array.map called on null or undefined');
    return [];
  }
  
  // Call the original map method with the thisArg
  try {
    return originalArrayMap.call(this, callbackfn, thisArg);
  } catch (error) {
    console.error('Error in Array.map:', error);
    return [];
  }
};

// Export a dummy function to ensure the file is imported and executed
export function ensureArrayPatchesLoaded() {
  return true;
}
