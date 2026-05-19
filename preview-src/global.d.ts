declare const d3: any;
declare const jsPlumb: any;

declare namespace d3 {
    interface Map<T> { }
    function map(): Map<any>;
}

interface JQueryStatic {
    isArray(obj: any): obj is any[];
    param: {
        fragment(params: any): string;
    };
    each<T>(collection: T[], callback: (index: number, item: T) => void | boolean): T[];
    each<T>(collection: T, callback: (index: any, item: any) => void | boolean): T;
}
