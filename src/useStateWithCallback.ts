import { useState, useRef, useEffect, useCallback } from 'react';

type LazyState<T> = [T, (newValue: React.SetStateAction<T>, callback?: (value: T) => void) => void];

export function useStateWithCallbackLazy<T>(initialValue: T): LazyState<T> {
    const callbackRef = useRef<(value: T) => void | null>(null);

    const [value, setValue] = useState<T>(initialValue);

    useEffect(() => {
        if (callbackRef.current) {
            callbackRef.current(value);
            // @ts-ignore
            callbackRef.current = null;
        }
    }, [value]);

    const setValueWithCallback = useCallback(
        (newValue: React.SetStateAction<T>, callback?: (value: T) => void) => {
            if (callback)
                // @ts-ignore
                callbackRef.current = callback;

            return setValue(newValue);
        },
        [],
    );

    return [value, setValueWithCallback];
};

type LazyStateAsync<T> = [T, (newValue: React.SetStateAction<T>, callback?: (value: T) => void) => Promise<T>];

export function useStateWithAsyncCallback<T>(initialValue: T): LazyStateAsync<T> {
    const [state, setState] = useStateWithCallbackLazy<T>(initialValue);

    return [
        state,
        (newValue: React.SetStateAction<T>, callback?: (value: T) => void): Promise<T> => {
            return new Promise((resolve) => {
                setState(newValue, (value) => {
                    resolve(value);
                    if (callback)
                        callback(value);
                })
            })
        }
    ]
}