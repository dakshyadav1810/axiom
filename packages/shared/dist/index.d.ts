import { z } from 'zod';

declare const ActionType: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
type ActionType = z.infer<typeof ActionType>;
declare const StepKind: z.ZodEnum<["ui", "api", "db"]>;
type StepKind = z.infer<typeof StepKind>;
declare const Generalization: z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>;
type Generalization = z.infer<typeof Generalization>;
declare const OnFailure: z.ZodEnum<["abort", "continue", "retry_once", "optional"]>;
type OnFailure = z.infer<typeof OnFailure>;
declare const SignalName: z.ZodEnum<["semantics", "affordance", "context", "structure", "index"]>;
type SignalName = z.infer<typeof SignalName>;
declare const Band: z.ZodEnum<["high", "medium", "low"]>;
type Band = z.infer<typeof Band>;
declare const ResolutionStatus: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
type ResolutionStatus = z.infer<typeof ResolutionStatus>;
declare const Score: z.ZodNumber;
type Score = z.infer<typeof Score>;

declare const Tier1Target: z.ZodObject<{
    label: z.ZodString;
    semantics: z.ZodArray<z.ZodString, "many">;
    role: z.ZodString;
    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
    intent: z.ZodString;
}, "strip", z.ZodTypeAny, {
    semantics: string[];
    label: string;
    role: string;
    actions: string[];
    intent: string;
}, {
    semantics: string[];
    label: string;
    role: string;
    intent: string;
    actions?: string[] | undefined;
}>;
type Tier1Target = z.infer<typeof Tier1Target>;

declare const Precondition: z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
    kind: z.ZodLiteral<"visible">;
}, "strip", z.ZodTypeAny, {
    kind: "visible";
}, {
    kind: "visible";
}>, z.ZodObject<{
    kind: z.ZodLiteral<"enabled">;
}, "strip", z.ZodTypeAny, {
    kind: "enabled";
}, {
    kind: "enabled";
}>, z.ZodObject<{
    kind: z.ZodLiteral<"modal_open">;
}, "strip", z.ZodTypeAny, {
    kind: "modal_open";
}, {
    kind: "modal_open";
}>, z.ZodObject<{
    kind: z.ZodLiteral<"url_contains">;
    value: z.ZodString;
}, "strip", z.ZodTypeAny, {
    value: string;
    kind: "url_contains";
}, {
    value: string;
    kind: "url_contains";
}>]>;
type Precondition = z.infer<typeof Precondition>;
declare const ExpectedOutcome: z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
    type: z.ZodLiteral<"navigation">;
}, "strip", z.ZodTypeAny, {
    type: "navigation";
}, {
    type: "navigation";
}>, z.ZodObject<{
    type: z.ZodLiteral<"url_change">;
    value: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "url_change";
    value: string;
}, {
    type: "url_change";
    value: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"element_appears">;
    value: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "element_appears";
    value: string;
}, {
    type: "element_appears";
    value: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"text_contains">;
    value: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "text_contains";
    value: string;
}, {
    type: "text_contains";
    value: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"field_contains">;
    value: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "field_contains";
    value: string;
}, {
    type: "field_contains";
    value: string;
}>]>;
type ExpectedOutcome = z.infer<typeof ExpectedOutcome>;
declare const Assertion: z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
    type: z.ZodLiteral<"urlContains">;
    expected: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "urlContains";
    expected: string;
}, {
    type: "urlContains";
    expected: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"textContains">;
    expected: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "textContains";
    expected: string;
}, {
    type: "textContains";
    expected: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"value">;
    expected: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "value";
    expected: string;
}, {
    type: "value";
    expected: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"elementVisible">;
    target: z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    }>;
}, "strip", z.ZodTypeAny, {
    type: "elementVisible";
    target: {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    };
}, {
    type: "elementVisible";
    target: {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    };
}>, z.ZodObject<{
    type: z.ZodLiteral<"elementAbsent">;
    target: z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    }>;
}, "strip", z.ZodTypeAny, {
    type: "elementAbsent";
    target: {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    };
}, {
    type: "elementAbsent";
    target: {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    };
}>, z.ZodObject<{
    type: z.ZodLiteral<"apiStatus">;
    expected: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    type: "apiStatus";
    expected: number;
}, {
    type: "apiStatus";
    expected: number;
}>, z.ZodObject<{
    type: z.ZodLiteral<"apiBody">;
    path: z.ZodString;
    expected: z.ZodUnknown;
}, "strip", z.ZodTypeAny, {
    type: "apiBody";
    path: string;
    expected?: unknown;
}, {
    type: "apiBody";
    path: string;
    expected?: unknown;
}>, z.ZodObject<{
    type: z.ZodLiteral<"dbRow">;
    query: z.ZodString;
    expected: z.ZodUnknown;
}, "strip", z.ZodTypeAny, {
    type: "dbRow";
    query: string;
    expected?: unknown;
}, {
    type: "dbRow";
    query: string;
    expected?: unknown;
}>]>;
type Assertion = z.infer<typeof Assertion>;
declare const UiStep: z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"ui">;
    action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
    value: z.ZodOptional<z.ZodString>;
    generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
    expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"navigation">;
    }, "strip", z.ZodTypeAny, {
        type: "navigation";
    }, {
        type: "navigation";
    }>, z.ZodObject<{
        type: z.ZodLiteral<"url_change">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "url_change";
        value: string;
    }, {
        type: "url_change";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"element_appears">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "element_appears";
        value: string;
    }, {
        type: "element_appears";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"text_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "text_contains";
        value: string;
    }, {
        type: "text_contains";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"field_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "field_contains";
        value: string;
    }, {
        type: "field_contains";
        value: string;
    }>]>, "many">>;
    target: z.ZodOptional<z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "ui";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
    expectedOutcome: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[];
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    } | undefined;
}, {
    intent: string;
    kind: "ui";
    id: string;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    } | undefined;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
    generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
    expectedOutcome?: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[] | undefined;
}>;
type UiStep = z.infer<typeof UiStep>;
declare const ApiStep: z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"api">;
    request: z.ZodObject<{
        method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
        url: z.ZodString;
        headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
        body: z.ZodOptional<z.ZodUnknown>;
    }, "strip", z.ZodTypeAny, {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    }, {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    }>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "api";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    request: {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    };
}, {
    intent: string;
    kind: "api";
    id: string;
    request: {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    };
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
}>;
type ApiStep = z.infer<typeof ApiStep>;
declare const DbStep: z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"db">;
    query: z.ZodString;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "db";
    query: string;
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
}, {
    intent: string;
    kind: "db";
    query: string;
    id: string;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
}>;
type DbStep = z.infer<typeof DbStep>;
declare const Step: z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"ui">;
    action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
    value: z.ZodOptional<z.ZodString>;
    generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
    expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"navigation">;
    }, "strip", z.ZodTypeAny, {
        type: "navigation";
    }, {
        type: "navigation";
    }>, z.ZodObject<{
        type: z.ZodLiteral<"url_change">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "url_change";
        value: string;
    }, {
        type: "url_change";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"element_appears">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "element_appears";
        value: string;
    }, {
        type: "element_appears";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"text_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "text_contains";
        value: string;
    }, {
        type: "text_contains";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"field_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "field_contains";
        value: string;
    }, {
        type: "field_contains";
        value: string;
    }>]>, "many">>;
    target: z.ZodOptional<z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "ui";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
    expectedOutcome: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[];
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    } | undefined;
}, {
    intent: string;
    kind: "ui";
    id: string;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    } | undefined;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
    generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
    expectedOutcome?: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[] | undefined;
}>, z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"api">;
    request: z.ZodObject<{
        method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
        url: z.ZodString;
        headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
        body: z.ZodOptional<z.ZodUnknown>;
    }, "strip", z.ZodTypeAny, {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    }, {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    }>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "api";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    request: {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    };
}, {
    intent: string;
    kind: "api";
    id: string;
    request: {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    };
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
}>, z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"db">;
    query: z.ZodString;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "db";
    query: string;
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
}, {
    intent: string;
    kind: "db";
    query: string;
    id: string;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
}>]>;
type Step = z.infer<typeof Step>;

declare const SpecIR: z.ZodObject<{
    version: z.ZodLiteral<"1.0">;
    flow: z.ZodObject<{
        id: z.ZodString;
        name: z.ZodString;
        intent: z.ZodString;
        startUrl: z.ZodString;
        vars: z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars: Record<string, string>;
    }, {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars?: Record<string, string> | undefined;
    }>;
    steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"ui">;
        action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
        value: z.ZodOptional<z.ZodString>;
        generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
        expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"navigation">;
        }, "strip", z.ZodTypeAny, {
            type: "navigation";
        }, {
            type: "navigation";
        }>, z.ZodObject<{
            type: z.ZodLiteral<"url_change">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "url_change";
            value: string;
        }, {
            type: "url_change";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"element_appears">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "element_appears";
            value: string;
        }, {
            type: "element_appears";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"text_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "text_contains";
            value: string;
        }, {
            type: "text_contains";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"field_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "field_contains";
            value: string;
        }, {
            type: "field_contains";
            value: string;
        }>]>, "many">>;
        target: z.ZodOptional<z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "ui";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
        expectedOutcome: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[];
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        } | undefined;
    }, {
        intent: string;
        kind: "ui";
        id: string;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        } | undefined;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
        generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
        expectedOutcome?: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[] | undefined;
    }>, z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"api">;
        request: z.ZodObject<{
            method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
            url: z.ZodString;
            headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
            body: z.ZodOptional<z.ZodUnknown>;
        }, "strip", z.ZodTypeAny, {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        }, {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        }>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "api";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
    }, {
        intent: string;
        kind: "api";
        id: string;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    }>, z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"db">;
        query: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
    }, {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    }>]>, "many">;
}, "strip", z.ZodTypeAny, {
    version: "1.0";
    flow: {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars: Record<string, string>;
    };
    steps: ({
        intent: string;
        kind: "ui";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
        expectedOutcome: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[];
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        } | undefined;
    } | {
        intent: string;
        kind: "api";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
    } | {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
    })[];
}, {
    version: "1.0";
    flow: {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars?: Record<string, string> | undefined;
    };
    steps: ({
        intent: string;
        kind: "ui";
        id: string;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        } | undefined;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
        generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
        expectedOutcome?: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[] | undefined;
    } | {
        intent: string;
        kind: "api";
        id: string;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    } | {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    })[];
}>;
type SpecIR = z.infer<typeof SpecIR>;
declare function lintSpec(spec: SpecIR): {
    ok: boolean;
    errors: string[];
};

declare const BoundingBox: z.ZodObject<{
    x: z.ZodNumber;
    y: z.ZodNumber;
    width: z.ZodNumber;
    height: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    x: number;
    y: number;
    width: number;
    height: number;
}, {
    x: number;
    y: number;
    width: number;
    height: number;
}>;
type BoundingBox = z.infer<typeof BoundingBox>;
declare const SignalScores: z.ZodObject<{
    semantics: z.ZodNumber;
    affordance: z.ZodNumber;
    context: z.ZodNumber;
    structure: z.ZodNumber;
    index: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    semantics: number;
    affordance: number;
    context: number;
    structure: number;
    index: number;
}, {
    semantics: number;
    affordance: number;
    context: number;
    structure: number;
    index: number;
}>;
type SignalScores = z.infer<typeof SignalScores>;
declare const Candidate: z.ZodObject<{
    id: z.ZodString;
    selector: z.ZodString;
    label: z.ZodOptional<z.ZodString>;
    role: z.ZodOptional<z.ZodString>;
    boundingBox: z.ZodOptional<z.ZodObject<{
        x: z.ZodNumber;
        y: z.ZodNumber;
        width: z.ZodNumber;
        height: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        x: number;
        y: number;
        width: number;
        height: number;
    }, {
        x: number;
        y: number;
        width: number;
        height: number;
    }>>;
    anchors: z.ZodDefault<z.ZodObject<{
        testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
        attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
        xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
        contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
        siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
        nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
    }, "strip", z.ZodTypeAny, {
        testId?: string | undefined;
        attributes?: Record<string, string> | undefined;
        xpath?: string | undefined;
        contextPath?: string[] | undefined;
        siblingIndex?: number | undefined;
        nearbyText?: string | undefined;
    }, {
        testId?: string | undefined;
        attributes?: Record<string, string> | undefined;
        xpath?: string | undefined;
        contextPath?: string[] | undefined;
        siblingIndex?: number | undefined;
        nearbyText?: string | undefined;
    }>>;
    signals: z.ZodObject<{
        semantics: z.ZodNumber;
        affordance: z.ZodNumber;
        context: z.ZodNumber;
        structure: z.ZodNumber;
        index: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        semantics: number;
        affordance: number;
        context: number;
        structure: number;
        index: number;
    }, {
        semantics: number;
        affordance: number;
        context: number;
        structure: number;
        index: number;
    }>;
    score: z.ZodNumber;
    band: z.ZodEnum<["high", "medium", "low"]>;
}, "strip", z.ZodTypeAny, {
    id: string;
    selector: string;
    anchors: {
        testId?: string | undefined;
        attributes?: Record<string, string> | undefined;
        xpath?: string | undefined;
        contextPath?: string[] | undefined;
        siblingIndex?: number | undefined;
        nearbyText?: string | undefined;
    };
    signals: {
        semantics: number;
        affordance: number;
        context: number;
        structure: number;
        index: number;
    };
    score: number;
    band: "high" | "medium" | "low";
    label?: string | undefined;
    role?: string | undefined;
    boundingBox?: {
        x: number;
        y: number;
        width: number;
        height: number;
    } | undefined;
}, {
    id: string;
    selector: string;
    signals: {
        semantics: number;
        affordance: number;
        context: number;
        structure: number;
        index: number;
    };
    score: number;
    band: "high" | "medium" | "low";
    label?: string | undefined;
    role?: string | undefined;
    boundingBox?: {
        x: number;
        y: number;
        width: number;
        height: number;
    } | undefined;
    anchors?: {
        testId?: string | undefined;
        attributes?: Record<string, string> | undefined;
        xpath?: string | undefined;
        contextPath?: string[] | undefined;
        siblingIndex?: number | undefined;
        nearbyText?: string | undefined;
    } | undefined;
}>;
type Candidate = z.infer<typeof Candidate>;

declare const Resolution: z.ZodObject<{
    status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
    confidence: z.ZodNumber;
    band: z.ZodEnum<["high", "medium", "low"]>;
    selected: z.ZodNullable<z.ZodString>;
    cachedSelector: z.ZodNullable<z.ZodString>;
    candidates: z.ZodArray<z.ZodObject<{
        id: z.ZodString;
        selector: z.ZodString;
        label: z.ZodOptional<z.ZodString>;
        role: z.ZodOptional<z.ZodString>;
        boundingBox: z.ZodOptional<z.ZodObject<{
            x: z.ZodNumber;
            y: z.ZodNumber;
            width: z.ZodNumber;
            height: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            x: number;
            y: number;
            width: number;
            height: number;
        }, {
            x: number;
            y: number;
            width: number;
            height: number;
        }>>;
        anchors: z.ZodDefault<z.ZodObject<{
            testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
            xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
            siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
            nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
        }, "strip", z.ZodTypeAny, {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        }, {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        }>>;
        signals: z.ZodObject<{
            semantics: z.ZodNumber;
            affordance: z.ZodNumber;
            context: z.ZodNumber;
            structure: z.ZodNumber;
            index: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        }, {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        }>;
        score: z.ZodNumber;
        band: z.ZodEnum<["high", "medium", "low"]>;
    }, "strip", z.ZodTypeAny, {
        id: string;
        selector: string;
        anchors: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        };
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
    }, {
        id: string;
        selector: string;
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
        anchors?: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        } | undefined;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    status: "grounded" | "ungrounded" | "stale";
    band: "high" | "medium" | "low";
    confidence: number;
    selected: string | null;
    cachedSelector: string | null;
    candidates: {
        id: string;
        selector: string;
        anchors: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        };
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
    }[];
}, {
    status: "grounded" | "ungrounded" | "stale";
    band: "high" | "medium" | "low";
    confidence: number;
    selected: string | null;
    cachedSelector: string | null;
    candidates: {
        id: string;
        selector: string;
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
        anchors?: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        } | undefined;
    }[];
}>;
type Resolution = z.infer<typeof Resolution>;
declare const GroundedResolution: z.ZodObject<Omit<{
    status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
    confidence: z.ZodNumber;
    band: z.ZodEnum<["high", "medium", "low"]>;
    selected: z.ZodNullable<z.ZodString>;
    cachedSelector: z.ZodNullable<z.ZodString>;
    candidates: z.ZodArray<z.ZodObject<{
        id: z.ZodString;
        selector: z.ZodString;
        label: z.ZodOptional<z.ZodString>;
        role: z.ZodOptional<z.ZodString>;
        boundingBox: z.ZodOptional<z.ZodObject<{
            x: z.ZodNumber;
            y: z.ZodNumber;
            width: z.ZodNumber;
            height: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            x: number;
            y: number;
            width: number;
            height: number;
        }, {
            x: number;
            y: number;
            width: number;
            height: number;
        }>>;
        anchors: z.ZodDefault<z.ZodObject<{
            testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
            xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
            siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
            nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
        }, "strip", z.ZodTypeAny, {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        }, {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        }>>;
        signals: z.ZodObject<{
            semantics: z.ZodNumber;
            affordance: z.ZodNumber;
            context: z.ZodNumber;
            structure: z.ZodNumber;
            index: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        }, {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        }>;
        score: z.ZodNumber;
        band: z.ZodEnum<["high", "medium", "low"]>;
    }, "strip", z.ZodTypeAny, {
        id: string;
        selector: string;
        anchors: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        };
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
    }, {
        id: string;
        selector: string;
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
        anchors?: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        } | undefined;
    }>, "many">;
}, "candidates"> & {
    winner: z.ZodNullable<z.ZodObject<{
        id: z.ZodString;
        selector: z.ZodString;
        label: z.ZodOptional<z.ZodString>;
        role: z.ZodOptional<z.ZodString>;
        boundingBox: z.ZodOptional<z.ZodObject<{
            x: z.ZodNumber;
            y: z.ZodNumber;
            width: z.ZodNumber;
            height: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            x: number;
            y: number;
            width: number;
            height: number;
        }, {
            x: number;
            y: number;
            width: number;
            height: number;
        }>>;
        anchors: z.ZodDefault<z.ZodObject<{
            testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
            xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
            siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
            nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
        }, "strip", z.ZodTypeAny, {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        }, {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        }>>;
        signals: z.ZodObject<{
            semantics: z.ZodNumber;
            affordance: z.ZodNumber;
            context: z.ZodNumber;
            structure: z.ZodNumber;
            index: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        }, {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        }>;
        score: z.ZodNumber;
        band: z.ZodEnum<["high", "medium", "low"]>;
    }, "strip", z.ZodTypeAny, {
        id: string;
        selector: string;
        anchors: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        };
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
    }, {
        id: string;
        selector: string;
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
        anchors?: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        } | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    status: "grounded" | "ungrounded" | "stale";
    band: "high" | "medium" | "low";
    confidence: number;
    selected: string | null;
    cachedSelector: string | null;
    winner: {
        id: string;
        selector: string;
        anchors: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        };
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
    } | null;
}, {
    status: "grounded" | "ungrounded" | "stale";
    band: "high" | "medium" | "low";
    confidence: number;
    selected: string | null;
    cachedSelector: string | null;
    winner: {
        id: string;
        selector: string;
        signals: {
            semantics: number;
            affordance: number;
            context: number;
            structure: number;
            index: number;
        };
        score: number;
        band: "high" | "medium" | "low";
        label?: string | undefined;
        role?: string | undefined;
        boundingBox?: {
            x: number;
            y: number;
            width: number;
            height: number;
        } | undefined;
        anchors?: {
            testId?: string | undefined;
            attributes?: Record<string, string> | undefined;
            xpath?: string | undefined;
            contextPath?: string[] | undefined;
            siblingIndex?: number | undefined;
            nearbyText?: string | undefined;
        } | undefined;
    } | null;
}>;
type GroundedResolution = z.infer<typeof GroundedResolution>;
declare const CandidatesDoc: z.ZodObject<{
    version: z.ZodLiteral<"1.0">;
    specId: z.ZodString;
    groundedAt: z.ZodString;
    groundedUrl: z.ZodString;
    steps: z.ZodArray<z.ZodObject<{
        stepId: z.ZodString;
        resolution: z.ZodObject<{
            status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
            confidence: z.ZodNumber;
            band: z.ZodEnum<["high", "medium", "low"]>;
            selected: z.ZodNullable<z.ZodString>;
            cachedSelector: z.ZodNullable<z.ZodString>;
            candidates: z.ZodArray<z.ZodObject<{
                id: z.ZodString;
                selector: z.ZodString;
                label: z.ZodOptional<z.ZodString>;
                role: z.ZodOptional<z.ZodString>;
                boundingBox: z.ZodOptional<z.ZodObject<{
                    x: z.ZodNumber;
                    y: z.ZodNumber;
                    width: z.ZodNumber;
                    height: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }>>;
                anchors: z.ZodDefault<z.ZodObject<{
                    testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                    xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                    siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                    nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                }, "strip", z.ZodTypeAny, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }>>;
                signals: z.ZodObject<{
                    semantics: z.ZodNumber;
                    affordance: z.ZodNumber;
                    context: z.ZodNumber;
                    structure: z.ZodNumber;
                    index: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }>;
                score: z.ZodNumber;
                band: z.ZodEnum<["high", "medium", "low"]>;
            }, "strip", z.ZodTypeAny, {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }, {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }>, "many">;
        }, "strip", z.ZodTypeAny, {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            candidates: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }[];
        }, {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            candidates: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }[];
        }>;
    }, "strip", z.ZodTypeAny, {
        stepId: string;
        resolution: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            candidates: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }[];
        };
    }, {
        stepId: string;
        resolution: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            candidates: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }[];
        };
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    version: "1.0";
    steps: {
        stepId: string;
        resolution: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            candidates: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }[];
        };
    }[];
    specId: string;
    groundedAt: string;
    groundedUrl: string;
}, {
    version: "1.0";
    steps: {
        stepId: string;
        resolution: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            candidates: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }[];
        };
    }[];
    specId: string;
    groundedAt: string;
    groundedUrl: string;
}>;
type CandidatesDoc = z.infer<typeof CandidatesDoc>;

declare const GroundedTarget: z.ZodObject<{
    label: z.ZodString;
    semantics: z.ZodArray<z.ZodString, "many">;
    role: z.ZodString;
    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
    intent: z.ZodString;
} & {
    resolution: z.ZodOptional<z.ZodObject<Omit<{
        status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
        confidence: z.ZodNumber;
        band: z.ZodEnum<["high", "medium", "low"]>;
        selected: z.ZodNullable<z.ZodString>;
        cachedSelector: z.ZodNullable<z.ZodString>;
        candidates: z.ZodArray<z.ZodObject<{
            id: z.ZodString;
            selector: z.ZodString;
            label: z.ZodOptional<z.ZodString>;
            role: z.ZodOptional<z.ZodString>;
            boundingBox: z.ZodOptional<z.ZodObject<{
                x: z.ZodNumber;
                y: z.ZodNumber;
                width: z.ZodNumber;
                height: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                x: number;
                y: number;
                width: number;
                height: number;
            }, {
                x: number;
                y: number;
                width: number;
                height: number;
            }>>;
            anchors: z.ZodDefault<z.ZodObject<{
                testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            }, "strip", z.ZodTypeAny, {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            }, {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            }>>;
            signals: z.ZodObject<{
                semantics: z.ZodNumber;
                affordance: z.ZodNumber;
                context: z.ZodNumber;
                structure: z.ZodNumber;
                index: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            }, {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            }>;
            score: z.ZodNumber;
            band: z.ZodEnum<["high", "medium", "low"]>;
        }, "strip", z.ZodTypeAny, {
            id: string;
            selector: string;
            anchors: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            };
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
        }, {
            id: string;
            selector: string;
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
            anchors?: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            } | undefined;
        }>, "many">;
    }, "candidates"> & {
        winner: z.ZodNullable<z.ZodObject<{
            id: z.ZodString;
            selector: z.ZodString;
            label: z.ZodOptional<z.ZodString>;
            role: z.ZodOptional<z.ZodString>;
            boundingBox: z.ZodOptional<z.ZodObject<{
                x: z.ZodNumber;
                y: z.ZodNumber;
                width: z.ZodNumber;
                height: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                x: number;
                y: number;
                width: number;
                height: number;
            }, {
                x: number;
                y: number;
                width: number;
                height: number;
            }>>;
            anchors: z.ZodDefault<z.ZodObject<{
                testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
            }, "strip", z.ZodTypeAny, {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            }, {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            }>>;
            signals: z.ZodObject<{
                semantics: z.ZodNumber;
                affordance: z.ZodNumber;
                context: z.ZodNumber;
                structure: z.ZodNumber;
                index: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            }, {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            }>;
            score: z.ZodNumber;
            band: z.ZodEnum<["high", "medium", "low"]>;
        }, "strip", z.ZodTypeAny, {
            id: string;
            selector: string;
            anchors: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            };
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
        }, {
            id: string;
            selector: string;
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
            anchors?: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            } | undefined;
        }>>;
    }, "strip", z.ZodTypeAny, {
        status: "grounded" | "ungrounded" | "stale";
        band: "high" | "medium" | "low";
        confidence: number;
        selected: string | null;
        cachedSelector: string | null;
        winner: {
            id: string;
            selector: string;
            anchors: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            };
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
        } | null;
    }, {
        status: "grounded" | "ungrounded" | "stale";
        band: "high" | "medium" | "low";
        confidence: number;
        selected: string | null;
        cachedSelector: string | null;
        winner: {
            id: string;
            selector: string;
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
            anchors?: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            } | undefined;
        } | null;
    }>>;
}, "strip", z.ZodTypeAny, {
    semantics: string[];
    label: string;
    role: string;
    actions: string[];
    intent: string;
    resolution?: {
        status: "grounded" | "ungrounded" | "stale";
        band: "high" | "medium" | "low";
        confidence: number;
        selected: string | null;
        cachedSelector: string | null;
        winner: {
            id: string;
            selector: string;
            anchors: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            };
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
        } | null;
    } | undefined;
}, {
    semantics: string[];
    label: string;
    role: string;
    intent: string;
    actions?: string[] | undefined;
    resolution?: {
        status: "grounded" | "ungrounded" | "stale";
        band: "high" | "medium" | "low";
        confidence: number;
        selected: string | null;
        cachedSelector: string | null;
        winner: {
            id: string;
            selector: string;
            signals: {
                semantics: number;
                affordance: number;
                context: number;
                structure: number;
                index: number;
            };
            score: number;
            band: "high" | "medium" | "low";
            label?: string | undefined;
            role?: string | undefined;
            boundingBox?: {
                x: number;
                y: number;
                width: number;
                height: number;
            } | undefined;
            anchors?: {
                testId?: string | undefined;
                attributes?: Record<string, string> | undefined;
                xpath?: string | undefined;
                contextPath?: string[] | undefined;
                siblingIndex?: number | undefined;
                nearbyText?: string | undefined;
            } | undefined;
        } | null;
    } | undefined;
}>;
type GroundedTarget = z.infer<typeof GroundedTarget>;
declare const GroundedUiStep: z.ZodObject<Omit<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"ui">;
    action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
    value: z.ZodOptional<z.ZodString>;
    generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
    expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"navigation">;
    }, "strip", z.ZodTypeAny, {
        type: "navigation";
    }, {
        type: "navigation";
    }>, z.ZodObject<{
        type: z.ZodLiteral<"url_change">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "url_change";
        value: string;
    }, {
        type: "url_change";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"element_appears">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "element_appears";
        value: string;
    }, {
        type: "element_appears";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"text_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "text_contains";
        value: string;
    }, {
        type: "text_contains";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"field_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "field_contains";
        value: string;
    }, {
        type: "field_contains";
        value: string;
    }>]>, "many">>;
    target: z.ZodOptional<z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    }>>;
}, "target"> & {
    target: z.ZodOptional<z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    } & {
        resolution: z.ZodOptional<z.ZodObject<Omit<{
            status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
            confidence: z.ZodNumber;
            band: z.ZodEnum<["high", "medium", "low"]>;
            selected: z.ZodNullable<z.ZodString>;
            cachedSelector: z.ZodNullable<z.ZodString>;
            candidates: z.ZodArray<z.ZodObject<{
                id: z.ZodString;
                selector: z.ZodString;
                label: z.ZodOptional<z.ZodString>;
                role: z.ZodOptional<z.ZodString>;
                boundingBox: z.ZodOptional<z.ZodObject<{
                    x: z.ZodNumber;
                    y: z.ZodNumber;
                    width: z.ZodNumber;
                    height: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }>>;
                anchors: z.ZodDefault<z.ZodObject<{
                    testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                    xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                    siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                    nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                }, "strip", z.ZodTypeAny, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }>>;
                signals: z.ZodObject<{
                    semantics: z.ZodNumber;
                    affordance: z.ZodNumber;
                    context: z.ZodNumber;
                    structure: z.ZodNumber;
                    index: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }>;
                score: z.ZodNumber;
                band: z.ZodEnum<["high", "medium", "low"]>;
            }, "strip", z.ZodTypeAny, {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }, {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }>, "many">;
        }, "candidates"> & {
            winner: z.ZodNullable<z.ZodObject<{
                id: z.ZodString;
                selector: z.ZodString;
                label: z.ZodOptional<z.ZodString>;
                role: z.ZodOptional<z.ZodString>;
                boundingBox: z.ZodOptional<z.ZodObject<{
                    x: z.ZodNumber;
                    y: z.ZodNumber;
                    width: z.ZodNumber;
                    height: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }>>;
                anchors: z.ZodDefault<z.ZodObject<{
                    testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                    xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                    siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                    nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                }, "strip", z.ZodTypeAny, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }>>;
                signals: z.ZodObject<{
                    semantics: z.ZodNumber;
                    affordance: z.ZodNumber;
                    context: z.ZodNumber;
                    structure: z.ZodNumber;
                    index: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }>;
                score: z.ZodNumber;
                band: z.ZodEnum<["high", "medium", "low"]>;
            }, "strip", z.ZodTypeAny, {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }, {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            } | null;
        }, {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            } | null;
        }>>;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            } | null;
        } | undefined;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            } | null;
        } | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "ui";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
    expectedOutcome: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[];
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            } | null;
        } | undefined;
    } | undefined;
}, {
    intent: string;
    kind: "ui";
    id: string;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            } | null;
        } | undefined;
    } | undefined;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
    generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
    expectedOutcome?: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[] | undefined;
}>;
type GroundedUiStep = z.infer<typeof GroundedUiStep>;
declare const GroundedStep: z.ZodDiscriminatedUnion<"kind", [z.ZodObject<Omit<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"ui">;
    action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
    value: z.ZodOptional<z.ZodString>;
    generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
    expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"navigation">;
    }, "strip", z.ZodTypeAny, {
        type: "navigation";
    }, {
        type: "navigation";
    }>, z.ZodObject<{
        type: z.ZodLiteral<"url_change">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "url_change";
        value: string;
    }, {
        type: "url_change";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"element_appears">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "element_appears";
        value: string;
    }, {
        type: "element_appears";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"text_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "text_contains";
        value: string;
    }, {
        type: "text_contains";
        value: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"field_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "field_contains";
        value: string;
    }, {
        type: "field_contains";
        value: string;
    }>]>, "many">>;
    target: z.ZodOptional<z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
    }>>;
}, "target"> & {
    target: z.ZodOptional<z.ZodObject<{
        label: z.ZodString;
        semantics: z.ZodArray<z.ZodString, "many">;
        role: z.ZodString;
        actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
        intent: z.ZodString;
    } & {
        resolution: z.ZodOptional<z.ZodObject<Omit<{
            status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
            confidence: z.ZodNumber;
            band: z.ZodEnum<["high", "medium", "low"]>;
            selected: z.ZodNullable<z.ZodString>;
            cachedSelector: z.ZodNullable<z.ZodString>;
            candidates: z.ZodArray<z.ZodObject<{
                id: z.ZodString;
                selector: z.ZodString;
                label: z.ZodOptional<z.ZodString>;
                role: z.ZodOptional<z.ZodString>;
                boundingBox: z.ZodOptional<z.ZodObject<{
                    x: z.ZodNumber;
                    y: z.ZodNumber;
                    width: z.ZodNumber;
                    height: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }>>;
                anchors: z.ZodDefault<z.ZodObject<{
                    testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                    xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                    siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                    nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                }, "strip", z.ZodTypeAny, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }>>;
                signals: z.ZodObject<{
                    semantics: z.ZodNumber;
                    affordance: z.ZodNumber;
                    context: z.ZodNumber;
                    structure: z.ZodNumber;
                    index: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }>;
                score: z.ZodNumber;
                band: z.ZodEnum<["high", "medium", "low"]>;
            }, "strip", z.ZodTypeAny, {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }, {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }>, "many">;
        }, "candidates"> & {
            winner: z.ZodNullable<z.ZodObject<{
                id: z.ZodString;
                selector: z.ZodString;
                label: z.ZodOptional<z.ZodString>;
                role: z.ZodOptional<z.ZodString>;
                boundingBox: z.ZodOptional<z.ZodObject<{
                    x: z.ZodNumber;
                    y: z.ZodNumber;
                    width: z.ZodNumber;
                    height: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }, {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                }>>;
                anchors: z.ZodDefault<z.ZodObject<{
                    testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                    xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                    siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                    nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                }, "strip", z.ZodTypeAny, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }, {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                }>>;
                signals: z.ZodObject<{
                    semantics: z.ZodNumber;
                    affordance: z.ZodNumber;
                    context: z.ZodNumber;
                    structure: z.ZodNumber;
                    index: z.ZodNumber;
                }, "strip", z.ZodTypeAny, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }, {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                }>;
                score: z.ZodNumber;
                band: z.ZodEnum<["high", "medium", "low"]>;
            }, "strip", z.ZodTypeAny, {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            }, {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            } | null;
        }, {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            } | null;
        }>>;
    }, "strip", z.ZodTypeAny, {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            } | null;
        } | undefined;
    }, {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            } | null;
        } | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "ui";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
    expectedOutcome: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[];
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        actions: string[];
        intent: string;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                anchors: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                };
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
            } | null;
        } | undefined;
    } | undefined;
}, {
    intent: string;
    kind: "ui";
    id: string;
    action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
    value?: string | undefined;
    target?: {
        semantics: string[];
        label: string;
        role: string;
        intent: string;
        actions?: string[] | undefined;
        resolution?: {
            status: "grounded" | "ungrounded" | "stale";
            band: "high" | "medium" | "low";
            confidence: number;
            selected: string | null;
            cachedSelector: string | null;
            winner: {
                id: string;
                selector: string;
                signals: {
                    semantics: number;
                    affordance: number;
                    context: number;
                    structure: number;
                    index: number;
                };
                score: number;
                band: "high" | "medium" | "low";
                label?: string | undefined;
                role?: string | undefined;
                boundingBox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                } | undefined;
                anchors?: {
                    testId?: string | undefined;
                    attributes?: Record<string, string> | undefined;
                    xpath?: string | undefined;
                    contextPath?: string[] | undefined;
                    siblingIndex?: number | undefined;
                    nearbyText?: string | undefined;
                } | undefined;
            } | null;
        } | undefined;
    } | undefined;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
    generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
    expectedOutcome?: ({
        type: "navigation";
    } | {
        type: "url_change";
        value: string;
    } | {
        type: "element_appears";
        value: string;
    } | {
        type: "text_contains";
        value: string;
    } | {
        type: "field_contains";
        value: string;
    })[] | undefined;
}>, z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"api">;
    request: z.ZodObject<{
        method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
        url: z.ZodString;
        headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
        body: z.ZodOptional<z.ZodUnknown>;
    }, "strip", z.ZodTypeAny, {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    }, {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    }>;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "api";
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
    request: {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    };
}, {
    intent: string;
    kind: "api";
    id: string;
    request: {
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
        url: string;
        headers?: Record<string, string> | undefined;
        body?: unknown;
    };
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
}>, z.ZodObject<{
    id: z.ZodString;
    intent: z.ZodString;
    onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
    preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        kind: z.ZodLiteral<"visible">;
    }, "strip", z.ZodTypeAny, {
        kind: "visible";
    }, {
        kind: "visible";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"enabled">;
    }, "strip", z.ZodTypeAny, {
        kind: "enabled";
    }, {
        kind: "enabled";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"modal_open">;
    }, "strip", z.ZodTypeAny, {
        kind: "modal_open";
    }, {
        kind: "modal_open";
    }>, z.ZodObject<{
        kind: z.ZodLiteral<"url_contains">;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        kind: "url_contains";
    }, {
        value: string;
        kind: "url_contains";
    }>]>, "many">>;
    assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
        type: z.ZodLiteral<"urlContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "urlContains";
        expected: string;
    }, {
        type: "urlContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"textContains">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "textContains";
        expected: string;
    }, {
        type: "textContains";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"value">;
        expected: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "value";
        expected: string;
    }, {
        type: "value";
        expected: string;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementVisible">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"elementAbsent">;
        target: z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>;
    }, "strip", z.ZodTypeAny, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    }, {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiStatus">;
        expected: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        type: "apiStatus";
        expected: number;
    }, {
        type: "apiStatus";
        expected: number;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"apiBody">;
        path: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }, {
        type: "apiBody";
        path: string;
        expected?: unknown;
    }>, z.ZodObject<{
        type: z.ZodLiteral<"dbRow">;
        query: z.ZodString;
        expected: z.ZodUnknown;
    }, "strip", z.ZodTypeAny, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }, {
        type: "dbRow";
        query: string;
        expected?: unknown;
    }>]>, "many">>;
    negative: z.ZodDefault<z.ZodBoolean>;
} & {
    kind: z.ZodLiteral<"db">;
    query: z.ZodString;
}, "strip", z.ZodTypeAny, {
    intent: string;
    kind: "db";
    query: string;
    id: string;
    onFailure: "abort" | "continue" | "retry_once" | "optional";
    preconditions: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[];
    assertions: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[];
    negative: boolean;
}, {
    intent: string;
    kind: "db";
    query: string;
    id: string;
    onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
    preconditions?: ({
        kind: "visible";
    } | {
        kind: "enabled";
    } | {
        kind: "modal_open";
    } | {
        value: string;
        kind: "url_contains";
    })[] | undefined;
    assertions?: ({
        type: "urlContains";
        expected: string;
    } | {
        type: "textContains";
        expected: string;
    } | {
        type: "value";
        expected: string;
    } | {
        type: "elementVisible";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "elementAbsent";
        target: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        };
    } | {
        type: "apiStatus";
        expected: number;
    } | {
        type: "apiBody";
        path: string;
        expected?: unknown;
    } | {
        type: "dbRow";
        query: string;
        expected?: unknown;
    })[] | undefined;
    negative?: boolean | undefined;
}>]>;
type GroundedStep = z.infer<typeof GroundedStep>;
declare const GroundedTest: z.ZodObject<Omit<{
    version: z.ZodLiteral<"1.0">;
    flow: z.ZodObject<{
        id: z.ZodString;
        name: z.ZodString;
        intent: z.ZodString;
        startUrl: z.ZodString;
        vars: z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars: Record<string, string>;
    }, {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars?: Record<string, string> | undefined;
    }>;
    steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"ui">;
        action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
        value: z.ZodOptional<z.ZodString>;
        generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
        expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"navigation">;
        }, "strip", z.ZodTypeAny, {
            type: "navigation";
        }, {
            type: "navigation";
        }>, z.ZodObject<{
            type: z.ZodLiteral<"url_change">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "url_change";
            value: string;
        }, {
            type: "url_change";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"element_appears">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "element_appears";
            value: string;
        }, {
            type: "element_appears";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"text_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "text_contains";
            value: string;
        }, {
            type: "text_contains";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"field_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "field_contains";
            value: string;
        }, {
            type: "field_contains";
            value: string;
        }>]>, "many">>;
        target: z.ZodOptional<z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "ui";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
        expectedOutcome: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[];
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        } | undefined;
    }, {
        intent: string;
        kind: "ui";
        id: string;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        } | undefined;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
        generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
        expectedOutcome?: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[] | undefined;
    }>, z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"api">;
        request: z.ZodObject<{
            method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
            url: z.ZodString;
            headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
            body: z.ZodOptional<z.ZodUnknown>;
        }, "strip", z.ZodTypeAny, {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        }, {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        }>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "api";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
    }, {
        intent: string;
        kind: "api";
        id: string;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    }>, z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"db">;
        query: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
    }, {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    }>]>, "many">;
}, "steps"> & {
    groundedAt: z.ZodString;
    groundedUrl: z.ZodString;
    steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<Omit<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"ui">;
        action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
        value: z.ZodOptional<z.ZodString>;
        generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
        expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"navigation">;
        }, "strip", z.ZodTypeAny, {
            type: "navigation";
        }, {
            type: "navigation";
        }>, z.ZodObject<{
            type: z.ZodLiteral<"url_change">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "url_change";
            value: string;
        }, {
            type: "url_change";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"element_appears">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "element_appears";
            value: string;
        }, {
            type: "element_appears";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"text_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "text_contains";
            value: string;
        }, {
            type: "text_contains";
            value: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"field_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "field_contains";
            value: string;
        }, {
            type: "field_contains";
            value: string;
        }>]>, "many">>;
        target: z.ZodOptional<z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
        }>>;
    }, "target"> & {
        target: z.ZodOptional<z.ZodObject<{
            label: z.ZodString;
            semantics: z.ZodArray<z.ZodString, "many">;
            role: z.ZodString;
            actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
            intent: z.ZodString;
        } & {
            resolution: z.ZodOptional<z.ZodObject<Omit<{
                status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
                confidence: z.ZodNumber;
                band: z.ZodEnum<["high", "medium", "low"]>;
                selected: z.ZodNullable<z.ZodString>;
                cachedSelector: z.ZodNullable<z.ZodString>;
                candidates: z.ZodArray<z.ZodObject<{
                    id: z.ZodString;
                    selector: z.ZodString;
                    label: z.ZodOptional<z.ZodString>;
                    role: z.ZodOptional<z.ZodString>;
                    boundingBox: z.ZodOptional<z.ZodObject<{
                        x: z.ZodNumber;
                        y: z.ZodNumber;
                        width: z.ZodNumber;
                        height: z.ZodNumber;
                    }, "strip", z.ZodTypeAny, {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    }, {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    }>>;
                    anchors: z.ZodDefault<z.ZodObject<{
                        testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                        attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                        xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                        contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                        siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                        nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    }, "strip", z.ZodTypeAny, {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    }, {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    }>>;
                    signals: z.ZodObject<{
                        semantics: z.ZodNumber;
                        affordance: z.ZodNumber;
                        context: z.ZodNumber;
                        structure: z.ZodNumber;
                        index: z.ZodNumber;
                    }, "strip", z.ZodTypeAny, {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    }, {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    }>;
                    score: z.ZodNumber;
                    band: z.ZodEnum<["high", "medium", "low"]>;
                }, "strip", z.ZodTypeAny, {
                    id: string;
                    selector: string;
                    anchors: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    };
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                }, {
                    id: string;
                    selector: string;
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                    anchors?: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    } | undefined;
                }>, "many">;
            }, "candidates"> & {
                winner: z.ZodNullable<z.ZodObject<{
                    id: z.ZodString;
                    selector: z.ZodString;
                    label: z.ZodOptional<z.ZodString>;
                    role: z.ZodOptional<z.ZodString>;
                    boundingBox: z.ZodOptional<z.ZodObject<{
                        x: z.ZodNumber;
                        y: z.ZodNumber;
                        width: z.ZodNumber;
                        height: z.ZodNumber;
                    }, "strip", z.ZodTypeAny, {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    }, {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    }>>;
                    anchors: z.ZodDefault<z.ZodObject<{
                        testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                        attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                        xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                        contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                        siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                        nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                    }, "strip", z.ZodTypeAny, {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    }, {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    }>>;
                    signals: z.ZodObject<{
                        semantics: z.ZodNumber;
                        affordance: z.ZodNumber;
                        context: z.ZodNumber;
                        structure: z.ZodNumber;
                        index: z.ZodNumber;
                    }, "strip", z.ZodTypeAny, {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    }, {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    }>;
                    score: z.ZodNumber;
                    band: z.ZodEnum<["high", "medium", "low"]>;
                }, "strip", z.ZodTypeAny, {
                    id: string;
                    selector: string;
                    anchors: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    };
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                }, {
                    id: string;
                    selector: string;
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                    anchors?: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    } | undefined;
                }>>;
            }, "strip", z.ZodTypeAny, {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    anchors: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    };
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                } | null;
            }, {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                    anchors?: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    } | undefined;
                } | null;
            }>>;
        }, "strip", z.ZodTypeAny, {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
            resolution?: {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    anchors: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    };
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                } | null;
            } | undefined;
        }, {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
            resolution?: {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                    anchors?: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    } | undefined;
                } | null;
            } | undefined;
        }>>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "ui";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
        expectedOutcome: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[];
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
            resolution?: {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    anchors: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    };
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                } | null;
            } | undefined;
        } | undefined;
    }, {
        intent: string;
        kind: "ui";
        id: string;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
            resolution?: {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                    anchors?: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    } | undefined;
                } | null;
            } | undefined;
        } | undefined;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
        generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
        expectedOutcome?: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[] | undefined;
    }>, z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"api">;
        request: z.ZodObject<{
            method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
            url: z.ZodString;
            headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
            body: z.ZodOptional<z.ZodUnknown>;
        }, "strip", z.ZodTypeAny, {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        }, {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        }>;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "api";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
    }, {
        intent: string;
        kind: "api";
        id: string;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    }>, z.ZodObject<{
        id: z.ZodString;
        intent: z.ZodString;
        onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
        preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            kind: z.ZodLiteral<"visible">;
        }, "strip", z.ZodTypeAny, {
            kind: "visible";
        }, {
            kind: "visible";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"enabled">;
        }, "strip", z.ZodTypeAny, {
            kind: "enabled";
        }, {
            kind: "enabled";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"modal_open">;
        }, "strip", z.ZodTypeAny, {
            kind: "modal_open";
        }, {
            kind: "modal_open";
        }>, z.ZodObject<{
            kind: z.ZodLiteral<"url_contains">;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            kind: "url_contains";
        }, {
            value: string;
            kind: "url_contains";
        }>]>, "many">>;
        assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
            type: z.ZodLiteral<"urlContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "urlContains";
            expected: string;
        }, {
            type: "urlContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"textContains">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "textContains";
            expected: string;
        }, {
            type: "textContains";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"value">;
            expected: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            type: "value";
            expected: string;
        }, {
            type: "value";
            expected: string;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementVisible">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"elementAbsent">;
            target: z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>;
        }, "strip", z.ZodTypeAny, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        }, {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiStatus">;
            expected: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            type: "apiStatus";
            expected: number;
        }, {
            type: "apiStatus";
            expected: number;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"apiBody">;
            path: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }, {
            type: "apiBody";
            path: string;
            expected?: unknown;
        }>, z.ZodObject<{
            type: z.ZodLiteral<"dbRow">;
            query: z.ZodString;
            expected: z.ZodUnknown;
        }, "strip", z.ZodTypeAny, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }, {
            type: "dbRow";
            query: string;
            expected?: unknown;
        }>]>, "many">>;
        negative: z.ZodDefault<z.ZodBoolean>;
    } & {
        kind: z.ZodLiteral<"db">;
        query: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
    }, {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    }>]>, "many">;
}, "strip", z.ZodTypeAny, {
    version: "1.0";
    flow: {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars: Record<string, string>;
    };
    steps: ({
        intent: string;
        kind: "api";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
    } | {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
    } | {
        intent: string;
        kind: "ui";
        id: string;
        onFailure: "abort" | "continue" | "retry_once" | "optional";
        preconditions: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[];
        assertions: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[];
        negative: boolean;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
        expectedOutcome: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[];
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            actions: string[];
            intent: string;
            resolution?: {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    anchors: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    };
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                } | null;
            } | undefined;
        } | undefined;
    })[];
    groundedAt: string;
    groundedUrl: string;
}, {
    version: "1.0";
    flow: {
        intent: string;
        id: string;
        name: string;
        startUrl: string;
        vars?: Record<string, string> | undefined;
    };
    steps: ({
        intent: string;
        kind: "api";
        id: string;
        request: {
            method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
            url: string;
            headers?: Record<string, string> | undefined;
            body?: unknown;
        };
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    } | {
        intent: string;
        kind: "db";
        query: string;
        id: string;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
    } | {
        intent: string;
        kind: "ui";
        id: string;
        action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
        value?: string | undefined;
        target?: {
            semantics: string[];
            label: string;
            role: string;
            intent: string;
            actions?: string[] | undefined;
            resolution?: {
                status: "grounded" | "ungrounded" | "stale";
                band: "high" | "medium" | "low";
                confidence: number;
                selected: string | null;
                cachedSelector: string | null;
                winner: {
                    id: string;
                    selector: string;
                    signals: {
                        semantics: number;
                        affordance: number;
                        context: number;
                        structure: number;
                        index: number;
                    };
                    score: number;
                    band: "high" | "medium" | "low";
                    label?: string | undefined;
                    role?: string | undefined;
                    boundingBox?: {
                        x: number;
                        y: number;
                        width: number;
                        height: number;
                    } | undefined;
                    anchors?: {
                        testId?: string | undefined;
                        attributes?: Record<string, string> | undefined;
                        xpath?: string | undefined;
                        contextPath?: string[] | undefined;
                        siblingIndex?: number | undefined;
                        nearbyText?: string | undefined;
                    } | undefined;
                } | null;
            } | undefined;
        } | undefined;
        onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
        preconditions?: ({
            kind: "visible";
        } | {
            kind: "enabled";
        } | {
            kind: "modal_open";
        } | {
            value: string;
            kind: "url_contains";
        })[] | undefined;
        assertions?: ({
            type: "urlContains";
            expected: string;
        } | {
            type: "textContains";
            expected: string;
        } | {
            type: "value";
            expected: string;
        } | {
            type: "elementVisible";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "elementAbsent";
            target: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            };
        } | {
            type: "apiStatus";
            expected: number;
        } | {
            type: "apiBody";
            path: string;
            expected?: unknown;
        } | {
            type: "dbRow";
            query: string;
            expected?: unknown;
        })[] | undefined;
        negative?: boolean | undefined;
        generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
        expectedOutcome?: ({
            type: "navigation";
        } | {
            type: "url_change";
            value: string;
        } | {
            type: "element_appears";
            value: string;
        } | {
            type: "text_contains";
            value: string;
        } | {
            type: "field_contains";
            value: string;
        })[] | undefined;
    })[];
    groundedAt: string;
    groundedUrl: string;
}>;
type GroundedTest = z.infer<typeof GroundedTest>;
declare function isStepGrounded(step: GroundedStep): boolean;

declare const AxiomConfig: z.ZodObject<{
    port: z.ZodDefault<z.ZodNumber>;
    browser: z.ZodDefault<z.ZodEnum<["chromium", "firefox", "webkit"]>>;
    headless: z.ZodDefault<z.ZodBoolean>;
    dbPath: z.ZodDefault<z.ZodString>;
    artifactsDir: z.ZodDefault<z.ZodString>;
    embeddingModel: z.ZodDefault<z.ZodString>;
    bands: z.ZodDefault<z.ZodObject<{
        high: z.ZodDefault<z.ZodNumber>;
        medium: z.ZodDefault<z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        high: number;
        medium: number;
    }, {
        high?: number | undefined;
        medium?: number | undefined;
    }>>;
    timeouts: z.ZodDefault<z.ZodObject<{
        actionMs: z.ZodDefault<z.ZodNumber>;
        navMs: z.ZodDefault<z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        actionMs: number;
        navMs: number;
    }, {
        actionMs?: number | undefined;
        navMs?: number | undefined;
    }>>;
    db: z.ZodDefault<z.ZodObject<{
        url: z.ZodOptional<z.ZodString>;
        readOnly: z.ZodDefault<z.ZodBoolean>;
    }, "strip", z.ZodTypeAny, {
        readOnly: boolean;
        url?: string | undefined;
    }, {
        url?: string | undefined;
        readOnly?: boolean | undefined;
    }>>;
}, "strip", z.ZodTypeAny, {
    db: {
        readOnly: boolean;
        url?: string | undefined;
    };
    port: number;
    browser: "chromium" | "firefox" | "webkit";
    headless: boolean;
    dbPath: string;
    artifactsDir: string;
    embeddingModel: string;
    bands: {
        high: number;
        medium: number;
    };
    timeouts: {
        actionMs: number;
        navMs: number;
    };
}, {
    db?: {
        url?: string | undefined;
        readOnly?: boolean | undefined;
    } | undefined;
    port?: number | undefined;
    browser?: "chromium" | "firefox" | "webkit" | undefined;
    headless?: boolean | undefined;
    dbPath?: string | undefined;
    artifactsDir?: string | undefined;
    embeddingModel?: string | undefined;
    bands?: {
        high?: number | undefined;
        medium?: number | undefined;
    } | undefined;
    timeouts?: {
        actionMs?: number | undefined;
        navMs?: number | undefined;
    } | undefined;
}>;
type AxiomConfig = z.infer<typeof AxiomConfig>;

declare const GroundRequest: z.ZodObject<{
    specId: z.ZodString;
}, "strip", z.ZodTypeAny, {
    specId: string;
}, {
    specId: string;
}>;
type GroundRequest = z.infer<typeof GroundRequest>;
declare const RunRequest: z.ZodObject<{
    testId: z.ZodString;
    vars: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
}, "strip", z.ZodTypeAny, {
    testId: string;
    vars?: Record<string, string> | undefined;
}, {
    testId: string;
    vars?: Record<string, string> | undefined;
}>;
type RunRequest = z.infer<typeof RunRequest>;
declare const MaintainRequest: z.ZodObject<{
    stepIds: z.ZodArray<z.ZodString, "many">;
    spec: z.ZodObject<{
        version: z.ZodLiteral<"1.0">;
        flow: z.ZodObject<{
            id: z.ZodString;
            name: z.ZodString;
            intent: z.ZodString;
            startUrl: z.ZodString;
            vars: z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        }, {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        }>;
        steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"ui">;
            action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
            value: z.ZodOptional<z.ZodString>;
            generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
            expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"navigation">;
            }, "strip", z.ZodTypeAny, {
                type: "navigation";
            }, {
                type: "navigation";
            }>, z.ZodObject<{
                type: z.ZodLiteral<"url_change">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "url_change";
                value: string;
            }, {
                type: "url_change";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"element_appears">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "element_appears";
                value: string;
            }, {
                type: "element_appears";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"text_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "text_contains";
                value: string;
            }, {
                type: "text_contains";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"field_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "field_contains";
                value: string;
            }, {
                type: "field_contains";
                value: string;
            }>]>, "many">>;
            target: z.ZodOptional<z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        }, {
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"api">;
            request: z.ZodObject<{
                method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
                url: z.ZodString;
                headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
                body: z.ZodOptional<z.ZodUnknown>;
            }, "strip", z.ZodTypeAny, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        }, {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"db">;
            query: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        }, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>]>, "many">;
    }, "strip", z.ZodTypeAny, {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        })[];
    }, {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        })[];
    }>;
}, "strip", z.ZodTypeAny, {
    stepIds: string[];
    spec: {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        })[];
    };
}, {
    stepIds: string[];
    spec: {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        })[];
    };
}>;
type MaintainRequest = z.infer<typeof MaintainRequest>;
declare const StepResult: z.ZodObject<{
    stepId: z.ZodString;
    status: z.ZodEnum<["passed", "failed", "warning", "skipped", "stale"]>;
    selection: z.ZodOptional<z.ZodEnum<["cached", "resolver", "none"]>>;
    band: z.ZodOptional<z.ZodEnum<["high", "medium", "low"]>>;
    failure: z.ZodOptional<z.ZodObject<{
        reason: z.ZodString;
        message: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        message: string;
        reason: string;
    }, {
        message: string;
        reason: string;
    }>>;
    durationMs: z.ZodNumber;
    screenshot: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    status: "stale" | "passed" | "failed" | "warning" | "skipped";
    stepId: string;
    durationMs: number;
    band?: "high" | "medium" | "low" | undefined;
    selection?: "cached" | "resolver" | "none" | undefined;
    failure?: {
        message: string;
        reason: string;
    } | undefined;
    screenshot?: string | undefined;
}, {
    status: "stale" | "passed" | "failed" | "warning" | "skipped";
    stepId: string;
    durationMs: number;
    band?: "high" | "medium" | "low" | undefined;
    selection?: "cached" | "resolver" | "none" | undefined;
    failure?: {
        message: string;
        reason: string;
    } | undefined;
    screenshot?: string | undefined;
}>;
type StepResult = z.infer<typeof StepResult>;
declare const RunReport: z.ZodObject<{
    runId: z.ZodString;
    testId: z.ZodString;
    status: z.ZodEnum<["passed", "failed"]>;
    needsReview: z.ZodDefault<z.ZodBoolean>;
    steps: z.ZodArray<z.ZodObject<{
        stepId: z.ZodString;
        status: z.ZodEnum<["passed", "failed", "warning", "skipped", "stale"]>;
        selection: z.ZodOptional<z.ZodEnum<["cached", "resolver", "none"]>>;
        band: z.ZodOptional<z.ZodEnum<["high", "medium", "low"]>>;
        failure: z.ZodOptional<z.ZodObject<{
            reason: z.ZodString;
            message: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            message: string;
            reason: string;
        }, {
            message: string;
            reason: string;
        }>>;
        durationMs: z.ZodNumber;
        screenshot: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    }, {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    }>, "many">;
    startedAt: z.ZodString;
    finishedAt: z.ZodString;
}, "strip", z.ZodTypeAny, {
    status: "passed" | "failed";
    steps: {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    }[];
    testId: string;
    runId: string;
    needsReview: boolean;
    startedAt: string;
    finishedAt: string;
}, {
    status: "passed" | "failed";
    steps: {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    }[];
    testId: string;
    runId: string;
    startedAt: string;
    finishedAt: string;
    needsReview?: boolean | undefined;
}>;
type RunReport = z.infer<typeof RunReport>;
declare const ApiError: z.ZodObject<{
    error: z.ZodObject<{
        code: z.ZodEnum<["validation", "not_found", "ungrounded", "stale", "browser_error"]>;
        message: z.ZodString;
        details: z.ZodOptional<z.ZodUnknown>;
    }, "strip", z.ZodTypeAny, {
        code: "validation" | "ungrounded" | "stale" | "not_found" | "browser_error";
        message: string;
        details?: unknown;
    }, {
        code: "validation" | "ungrounded" | "stale" | "not_found" | "browser_error";
        message: string;
        details?: unknown;
    }>;
}, "strip", z.ZodTypeAny, {
    error: {
        code: "validation" | "ungrounded" | "stale" | "not_found" | "browser_error";
        message: string;
        details?: unknown;
    };
}, {
    error: {
        code: "validation" | "ungrounded" | "stale" | "not_found" | "browser_error";
        message: string;
        details?: unknown;
    };
}>;
type ApiError = z.infer<typeof ApiError>;
declare const RepairPayload: z.ZodObject<{
    specIR: z.ZodObject<{
        version: z.ZodLiteral<"1.0">;
        flow: z.ZodObject<{
            id: z.ZodString;
            name: z.ZodString;
            intent: z.ZodString;
            startUrl: z.ZodString;
            vars: z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        }, {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        }>;
        steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"ui">;
            action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
            value: z.ZodOptional<z.ZodString>;
            generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
            expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"navigation">;
            }, "strip", z.ZodTypeAny, {
                type: "navigation";
            }, {
                type: "navigation";
            }>, z.ZodObject<{
                type: z.ZodLiteral<"url_change">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "url_change";
                value: string;
            }, {
                type: "url_change";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"element_appears">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "element_appears";
                value: string;
            }, {
                type: "element_appears";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"text_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "text_contains";
                value: string;
            }, {
                type: "text_contains";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"field_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "field_contains";
                value: string;
            }, {
                type: "field_contains";
                value: string;
            }>]>, "many">>;
            target: z.ZodOptional<z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        }, {
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"api">;
            request: z.ZodObject<{
                method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
                url: z.ZodString;
                headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
                body: z.ZodOptional<z.ZodUnknown>;
            }, "strip", z.ZodTypeAny, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        }, {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"db">;
            query: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        }, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>]>, "many">;
    }, "strip", z.ZodTypeAny, {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        })[];
    }, {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        })[];
    }>;
    testCase: z.ZodObject<Omit<{
        version: z.ZodLiteral<"1.0">;
        flow: z.ZodObject<{
            id: z.ZodString;
            name: z.ZodString;
            intent: z.ZodString;
            startUrl: z.ZodString;
            vars: z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        }, {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        }>;
        steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"ui">;
            action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
            value: z.ZodOptional<z.ZodString>;
            generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
            expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"navigation">;
            }, "strip", z.ZodTypeAny, {
                type: "navigation";
            }, {
                type: "navigation";
            }>, z.ZodObject<{
                type: z.ZodLiteral<"url_change">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "url_change";
                value: string;
            }, {
                type: "url_change";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"element_appears">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "element_appears";
                value: string;
            }, {
                type: "element_appears";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"text_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "text_contains";
                value: string;
            }, {
                type: "text_contains";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"field_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "field_contains";
                value: string;
            }, {
                type: "field_contains";
                value: string;
            }>]>, "many">>;
            target: z.ZodOptional<z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        }, {
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"api">;
            request: z.ZodObject<{
                method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
                url: z.ZodString;
                headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
                body: z.ZodOptional<z.ZodUnknown>;
            }, "strip", z.ZodTypeAny, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        }, {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"db">;
            query: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        }, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>]>, "many">;
    }, "steps"> & {
        groundedAt: z.ZodString;
        groundedUrl: z.ZodString;
        steps: z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<Omit<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"ui">;
            action: z.ZodEnum<["navigate", "click", "type", "select", "keypress", "submit", "wait"]>;
            value: z.ZodOptional<z.ZodString>;
            generalization: z.ZodDefault<z.ZodEnum<["same_element", "any_matching", "aggressive", "flexible"]>>;
            expectedOutcome: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"navigation">;
            }, "strip", z.ZodTypeAny, {
                type: "navigation";
            }, {
                type: "navigation";
            }>, z.ZodObject<{
                type: z.ZodLiteral<"url_change">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "url_change";
                value: string;
            }, {
                type: "url_change";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"element_appears">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "element_appears";
                value: string;
            }, {
                type: "element_appears";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"text_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "text_contains";
                value: string;
            }, {
                type: "text_contains";
                value: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"field_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "field_contains";
                value: string;
            }, {
                type: "field_contains";
                value: string;
            }>]>, "many">>;
            target: z.ZodOptional<z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            }>>;
        }, "target"> & {
            target: z.ZodOptional<z.ZodObject<{
                label: z.ZodString;
                semantics: z.ZodArray<z.ZodString, "many">;
                role: z.ZodString;
                actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                intent: z.ZodString;
            } & {
                resolution: z.ZodOptional<z.ZodObject<Omit<{
                    status: z.ZodEnum<["grounded", "ungrounded", "stale"]>;
                    confidence: z.ZodNumber;
                    band: z.ZodEnum<["high", "medium", "low"]>;
                    selected: z.ZodNullable<z.ZodString>;
                    cachedSelector: z.ZodNullable<z.ZodString>;
                    candidates: z.ZodArray<z.ZodObject<{
                        id: z.ZodString;
                        selector: z.ZodString;
                        label: z.ZodOptional<z.ZodString>;
                        role: z.ZodOptional<z.ZodString>;
                        boundingBox: z.ZodOptional<z.ZodObject<{
                            x: z.ZodNumber;
                            y: z.ZodNumber;
                            width: z.ZodNumber;
                            height: z.ZodNumber;
                        }, "strip", z.ZodTypeAny, {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        }, {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        }>>;
                        anchors: z.ZodDefault<z.ZodObject<{
                            testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                            attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                            xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                            contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                            siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                            nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                        }, "strip", z.ZodTypeAny, {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        }, {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        }>>;
                        signals: z.ZodObject<{
                            semantics: z.ZodNumber;
                            affordance: z.ZodNumber;
                            context: z.ZodNumber;
                            structure: z.ZodNumber;
                            index: z.ZodNumber;
                        }, "strip", z.ZodTypeAny, {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        }, {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        }>;
                        score: z.ZodNumber;
                        band: z.ZodEnum<["high", "medium", "low"]>;
                    }, "strip", z.ZodTypeAny, {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    }, {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    }>, "many">;
                }, "candidates"> & {
                    winner: z.ZodNullable<z.ZodObject<{
                        id: z.ZodString;
                        selector: z.ZodString;
                        label: z.ZodOptional<z.ZodString>;
                        role: z.ZodOptional<z.ZodString>;
                        boundingBox: z.ZodOptional<z.ZodObject<{
                            x: z.ZodNumber;
                            y: z.ZodNumber;
                            width: z.ZodNumber;
                            height: z.ZodNumber;
                        }, "strip", z.ZodTypeAny, {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        }, {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        }>>;
                        anchors: z.ZodDefault<z.ZodObject<{
                            testId: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                            attributes: z.ZodOptional<z.ZodDefault<z.ZodRecord<z.ZodString, z.ZodString>>>;
                            xpath: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                            contextPath: z.ZodOptional<z.ZodDefault<z.ZodArray<z.ZodString, "many">>>;
                            siblingIndex: z.ZodOptional<z.ZodOptional<z.ZodNumber>>;
                            nearbyText: z.ZodOptional<z.ZodOptional<z.ZodString>>;
                        }, "strip", z.ZodTypeAny, {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        }, {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        }>>;
                        signals: z.ZodObject<{
                            semantics: z.ZodNumber;
                            affordance: z.ZodNumber;
                            context: z.ZodNumber;
                            structure: z.ZodNumber;
                            index: z.ZodNumber;
                        }, "strip", z.ZodTypeAny, {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        }, {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        }>;
                        score: z.ZodNumber;
                        band: z.ZodEnum<["high", "medium", "low"]>;
                    }, "strip", z.ZodTypeAny, {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    }, {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    }>>;
                }, "strip", z.ZodTypeAny, {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    } | null;
                }, {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    } | null;
                }>>;
            }, "strip", z.ZodTypeAny, {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    } | null;
                } | undefined;
            }, {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    } | null;
                } | undefined;
            }>>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    } | null;
                } | undefined;
            } | undefined;
        }, {
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    } | null;
                } | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"api">;
            request: z.ZodObject<{
                method: z.ZodEnum<["GET", "POST", "PUT", "PATCH", "DELETE"]>;
                url: z.ZodString;
                headers: z.ZodOptional<z.ZodRecord<z.ZodString, z.ZodString>>;
                body: z.ZodOptional<z.ZodUnknown>;
            }, "strip", z.ZodTypeAny, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }, {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            }>;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        }, {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>, z.ZodObject<{
            id: z.ZodString;
            intent: z.ZodString;
            onFailure: z.ZodDefault<z.ZodEnum<["abort", "continue", "retry_once", "optional"]>>;
            preconditions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"kind", [z.ZodObject<{
                kind: z.ZodLiteral<"visible">;
            }, "strip", z.ZodTypeAny, {
                kind: "visible";
            }, {
                kind: "visible";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"enabled">;
            }, "strip", z.ZodTypeAny, {
                kind: "enabled";
            }, {
                kind: "enabled";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"modal_open">;
            }, "strip", z.ZodTypeAny, {
                kind: "modal_open";
            }, {
                kind: "modal_open";
            }>, z.ZodObject<{
                kind: z.ZodLiteral<"url_contains">;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                kind: "url_contains";
            }, {
                value: string;
                kind: "url_contains";
            }>]>, "many">>;
            assertions: z.ZodDefault<z.ZodArray<z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
                type: z.ZodLiteral<"urlContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "urlContains";
                expected: string;
            }, {
                type: "urlContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"textContains">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "textContains";
                expected: string;
            }, {
                type: "textContains";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"value">;
                expected: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                type: "value";
                expected: string;
            }, {
                type: "value";
                expected: string;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementVisible">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"elementAbsent">;
                target: z.ZodObject<{
                    label: z.ZodString;
                    semantics: z.ZodArray<z.ZodString, "many">;
                    role: z.ZodString;
                    actions: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
                    intent: z.ZodString;
                }, "strip", z.ZodTypeAny, {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                }, {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                }>;
            }, "strip", z.ZodTypeAny, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            }, {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiStatus">;
                expected: z.ZodNumber;
            }, "strip", z.ZodTypeAny, {
                type: "apiStatus";
                expected: number;
            }, {
                type: "apiStatus";
                expected: number;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"apiBody">;
                path: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }, {
                type: "apiBody";
                path: string;
                expected?: unknown;
            }>, z.ZodObject<{
                type: z.ZodLiteral<"dbRow">;
                query: z.ZodString;
                expected: z.ZodUnknown;
            }, "strip", z.ZodTypeAny, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }, {
                type: "dbRow";
                query: string;
                expected?: unknown;
            }>]>, "many">>;
            negative: z.ZodDefault<z.ZodBoolean>;
        } & {
            kind: z.ZodLiteral<"db">;
            query: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        }, {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        }>]>, "many">;
    }, "strip", z.ZodTypeAny, {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        };
        steps: ({
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        } | {
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    } | null;
                } | undefined;
            } | undefined;
        })[];
        groundedAt: string;
        groundedUrl: string;
    }, {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        };
        steps: ({
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    } | null;
                } | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        })[];
        groundedAt: string;
        groundedUrl: string;
    }>;
    kdg: z.ZodUnknown;
}, "strip", z.ZodTypeAny, {
    specIR: {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
            } | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        })[];
    };
    testCase: {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars: Record<string, string>;
        };
        steps: ({
            intent: string;
            kind: "api";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
        } | {
            intent: string;
            kind: "ui";
            id: string;
            onFailure: "abort" | "continue" | "retry_once" | "optional";
            preconditions: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[];
            assertions: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    actions: string[];
                    intent: string;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[];
            negative: boolean;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            generalization: "same_element" | "any_matching" | "aggressive" | "flexible";
            expectedOutcome: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[];
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                actions: string[];
                intent: string;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        anchors: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        };
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                    } | null;
                } | undefined;
            } | undefined;
        })[];
        groundedAt: string;
        groundedUrl: string;
    };
    kdg?: unknown;
}, {
    specIR: {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        };
        steps: ({
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        } | {
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        })[];
    };
    testCase: {
        version: "1.0";
        flow: {
            intent: string;
            id: string;
            name: string;
            startUrl: string;
            vars?: Record<string, string> | undefined;
        };
        steps: ({
            intent: string;
            kind: "api";
            id: string;
            request: {
                method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
                url: string;
                headers?: Record<string, string> | undefined;
                body?: unknown;
            };
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "db";
            query: string;
            id: string;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
        } | {
            intent: string;
            kind: "ui";
            id: string;
            action: "navigate" | "click" | "type" | "select" | "keypress" | "submit" | "wait";
            value?: string | undefined;
            target?: {
                semantics: string[];
                label: string;
                role: string;
                intent: string;
                actions?: string[] | undefined;
                resolution?: {
                    status: "grounded" | "ungrounded" | "stale";
                    band: "high" | "medium" | "low";
                    confidence: number;
                    selected: string | null;
                    cachedSelector: string | null;
                    winner: {
                        id: string;
                        selector: string;
                        signals: {
                            semantics: number;
                            affordance: number;
                            context: number;
                            structure: number;
                            index: number;
                        };
                        score: number;
                        band: "high" | "medium" | "low";
                        label?: string | undefined;
                        role?: string | undefined;
                        boundingBox?: {
                            x: number;
                            y: number;
                            width: number;
                            height: number;
                        } | undefined;
                        anchors?: {
                            testId?: string | undefined;
                            attributes?: Record<string, string> | undefined;
                            xpath?: string | undefined;
                            contextPath?: string[] | undefined;
                            siblingIndex?: number | undefined;
                            nearbyText?: string | undefined;
                        } | undefined;
                    } | null;
                } | undefined;
            } | undefined;
            onFailure?: "abort" | "continue" | "retry_once" | "optional" | undefined;
            preconditions?: ({
                kind: "visible";
            } | {
                kind: "enabled";
            } | {
                kind: "modal_open";
            } | {
                value: string;
                kind: "url_contains";
            })[] | undefined;
            assertions?: ({
                type: "urlContains";
                expected: string;
            } | {
                type: "textContains";
                expected: string;
            } | {
                type: "value";
                expected: string;
            } | {
                type: "elementVisible";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "elementAbsent";
                target: {
                    semantics: string[];
                    label: string;
                    role: string;
                    intent: string;
                    actions?: string[] | undefined;
                };
            } | {
                type: "apiStatus";
                expected: number;
            } | {
                type: "apiBody";
                path: string;
                expected?: unknown;
            } | {
                type: "dbRow";
                query: string;
                expected?: unknown;
            })[] | undefined;
            negative?: boolean | undefined;
            generalization?: "same_element" | "any_matching" | "aggressive" | "flexible" | undefined;
            expectedOutcome?: ({
                type: "navigation";
            } | {
                type: "url_change";
                value: string;
            } | {
                type: "element_appears";
                value: string;
            } | {
                type: "text_contains";
                value: string;
            } | {
                type: "field_contains";
                value: string;
            })[] | undefined;
        })[];
        groundedAt: string;
        groundedUrl: string;
    };
    kdg?: unknown;
}>;
type RepairPayload = z.infer<typeof RepairPayload>;

declare const WsMessage: z.ZodDiscriminatedUnion<"type", [z.ZodObject<{
    type: z.ZodLiteral<"run.start">;
    runId: z.ZodString;
    testId: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "run.start";
    testId: string;
    runId: string;
}, {
    type: "run.start";
    testId: string;
    runId: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"step.start">;
    stepId: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "step.start";
    stepId: string;
}, {
    type: "step.start";
    stepId: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"resolver.event">;
    stepId: z.ZodString;
    band: z.ZodEnum<["high", "medium", "low"]>;
    selected: z.ZodNullable<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    type: "resolver.event";
    band: "high" | "medium" | "low";
    selected: string | null;
    stepId: string;
}, {
    type: "resolver.event";
    band: "high" | "medium" | "low";
    selected: string | null;
    stepId: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"step.result">;
    result: z.ZodObject<{
        stepId: z.ZodString;
        status: z.ZodEnum<["passed", "failed", "warning", "skipped", "stale"]>;
        selection: z.ZodOptional<z.ZodEnum<["cached", "resolver", "none"]>>;
        band: z.ZodOptional<z.ZodEnum<["high", "medium", "low"]>>;
        failure: z.ZodOptional<z.ZodObject<{
            reason: z.ZodString;
            message: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            message: string;
            reason: string;
        }, {
            message: string;
            reason: string;
        }>>;
        durationMs: z.ZodNumber;
        screenshot: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    }, {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    }>;
}, "strip", z.ZodTypeAny, {
    type: "step.result";
    result: {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    };
}, {
    type: "step.result";
    result: {
        status: "stale" | "passed" | "failed" | "warning" | "skipped";
        stepId: string;
        durationMs: number;
        band?: "high" | "medium" | "low" | undefined;
        selection?: "cached" | "resolver" | "none" | undefined;
        failure?: {
            message: string;
            reason: string;
        } | undefined;
        screenshot?: string | undefined;
    };
}>, z.ZodObject<{
    type: z.ZodLiteral<"log">;
    level: z.ZodEnum<["info", "warn", "error"]>;
    line: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "log";
    level: "error" | "info" | "warn";
    line: string;
}, {
    type: "log";
    level: "error" | "info" | "warn";
    line: string;
}>, z.ZodObject<{
    type: z.ZodLiteral<"run.complete">;
    report: z.ZodObject<{
        runId: z.ZodString;
        testId: z.ZodString;
        status: z.ZodEnum<["passed", "failed"]>;
        needsReview: z.ZodDefault<z.ZodBoolean>;
        steps: z.ZodArray<z.ZodObject<{
            stepId: z.ZodString;
            status: z.ZodEnum<["passed", "failed", "warning", "skipped", "stale"]>;
            selection: z.ZodOptional<z.ZodEnum<["cached", "resolver", "none"]>>;
            band: z.ZodOptional<z.ZodEnum<["high", "medium", "low"]>>;
            failure: z.ZodOptional<z.ZodObject<{
                reason: z.ZodString;
                message: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                message: string;
                reason: string;
            }, {
                message: string;
                reason: string;
            }>>;
            durationMs: z.ZodNumber;
            screenshot: z.ZodOptional<z.ZodString>;
        }, "strip", z.ZodTypeAny, {
            status: "stale" | "passed" | "failed" | "warning" | "skipped";
            stepId: string;
            durationMs: number;
            band?: "high" | "medium" | "low" | undefined;
            selection?: "cached" | "resolver" | "none" | undefined;
            failure?: {
                message: string;
                reason: string;
            } | undefined;
            screenshot?: string | undefined;
        }, {
            status: "stale" | "passed" | "failed" | "warning" | "skipped";
            stepId: string;
            durationMs: number;
            band?: "high" | "medium" | "low" | undefined;
            selection?: "cached" | "resolver" | "none" | undefined;
            failure?: {
                message: string;
                reason: string;
            } | undefined;
            screenshot?: string | undefined;
        }>, "many">;
        startedAt: z.ZodString;
        finishedAt: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        status: "passed" | "failed";
        steps: {
            status: "stale" | "passed" | "failed" | "warning" | "skipped";
            stepId: string;
            durationMs: number;
            band?: "high" | "medium" | "low" | undefined;
            selection?: "cached" | "resolver" | "none" | undefined;
            failure?: {
                message: string;
                reason: string;
            } | undefined;
            screenshot?: string | undefined;
        }[];
        testId: string;
        runId: string;
        needsReview: boolean;
        startedAt: string;
        finishedAt: string;
    }, {
        status: "passed" | "failed";
        steps: {
            status: "stale" | "passed" | "failed" | "warning" | "skipped";
            stepId: string;
            durationMs: number;
            band?: "high" | "medium" | "low" | undefined;
            selection?: "cached" | "resolver" | "none" | undefined;
            failure?: {
                message: string;
                reason: string;
            } | undefined;
            screenshot?: string | undefined;
        }[];
        testId: string;
        runId: string;
        startedAt: string;
        finishedAt: string;
        needsReview?: boolean | undefined;
    }>;
}, "strip", z.ZodTypeAny, {
    type: "run.complete";
    report: {
        status: "passed" | "failed";
        steps: {
            status: "stale" | "passed" | "failed" | "warning" | "skipped";
            stepId: string;
            durationMs: number;
            band?: "high" | "medium" | "low" | undefined;
            selection?: "cached" | "resolver" | "none" | undefined;
            failure?: {
                message: string;
                reason: string;
            } | undefined;
            screenshot?: string | undefined;
        }[];
        testId: string;
        runId: string;
        needsReview: boolean;
        startedAt: string;
        finishedAt: string;
    };
}, {
    type: "run.complete";
    report: {
        status: "passed" | "failed";
        steps: {
            status: "stale" | "passed" | "failed" | "warning" | "skipped";
            stepId: string;
            durationMs: number;
            band?: "high" | "medium" | "low" | undefined;
            selection?: "cached" | "resolver" | "none" | undefined;
            failure?: {
                message: string;
                reason: string;
            } | undefined;
            screenshot?: string | undefined;
        }[];
        testId: string;
        runId: string;
        startedAt: string;
        finishedAt: string;
        needsReview?: boolean | undefined;
    };
}>]>;
type WsMessage = z.infer<typeof WsMessage>;

export { ActionType, ApiError, ApiStep, Assertion, AxiomConfig, Band, BoundingBox, Candidate, CandidatesDoc, DbStep, ExpectedOutcome, Generalization, GroundRequest, GroundedResolution, GroundedStep, GroundedTarget, GroundedTest, GroundedUiStep, MaintainRequest, OnFailure, Precondition, RepairPayload, Resolution, ResolutionStatus, RunReport, RunRequest, Score, SignalName, SignalScores, SpecIR, Step, StepKind, StepResult, Tier1Target, UiStep, WsMessage, isStepGrounded, lintSpec };
