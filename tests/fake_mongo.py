"""A tiny in-memory stand-in for a MongoDB collection, used by the API tests.

It understands only the query operators and aggregation stages that PuneBite's API and
chatbot use ($match, $group, $unwind, $bucket, $sort, $limit ...), so the whole API can be
tested without a database server. It is NOT a general MongoDB emulator.
"""
import re

COMPARE = {
    "$gte": lambda a, b: a >= b,
    "$lte": lambda a, b: a <= b,
    "$gt": lambda a, b: a > b,
    "$lt": lambda a, b: a < b,
}


# ------------------------------------------------------------------- queries
def _value_matches(value, cond):
    values = value if isinstance(value, list) else [value]
    if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
        for op, arg in cond.items():
            if op == "$options":
                continue
            if op == "$regex":
                flags = re.I if "i" in cond.get("$options", "") else 0
                if not any(v is not None and re.search(arg, str(v), flags) for v in values):
                    return False
            elif op == "$in":
                if not any(v in arg for v in values):
                    return False
            elif op == "$ne":
                if (value is None) if arg is None else (arg in values):
                    return False
            elif op in COMPARE:
                if not any(v is not None and COMPARE[op](v, arg) for v in values):
                    return False
            else:
                raise NotImplementedError(op)
        return True
    return cond in values


def matches(doc, query):
    for key, cond in query.items():
        if key == "$and":
            if not all(matches(doc, sub) for sub in cond):
                return False
        elif not _value_matches(doc.get(key), cond):
            return False
    return True


def sort_docs(docs, spec):
    """spec = [(field, 1 or -1), ...]; missing values sort lowest, as in MongoDB."""
    docs = list(docs)
    for field, direction in reversed(list(spec)):
        docs.sort(key=lambda d, f=field: (d.get(f) is not None, d.get(f) if d.get(f) is not None else 0),
                  reverse=direction == -1)
    return docs


def project(doc, projection):
    if not projection:
        return dict(doc)
    include = [k for k, v in projection.items() if v and k != "_id"]
    if include:
        return {k: doc.get(k) for k in include}
    return {k: v for k, v in doc.items() if not (k in projection and projection[k] == 0)}


# ---------------------------------------------------------------- aggregation
def evaluate(expr, doc):
    if isinstance(expr, str) and expr.startswith("$"):
        return doc.get(expr[1:])
    if isinstance(expr, dict):
        (op, args), = expr.items()
        if op == "$cond":
            test, yes, no = args
            return evaluate(yes, doc) if evaluate(test, doc) else evaluate(no, doc)
        a, b = (evaluate(x, doc) for x in args)
        if op == "$ne":
            return a != b
        if op in COMPARE:
            return a is not None and b is not None and COMPARE[op](a, b)
        raise NotImplementedError(op)
    return expr


def _accumulate(spec, docs):
    (op, expr), = spec.items()
    values = [evaluate(expr, d) for d in docs]
    numbers = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if op == "$sum":
        return sum(numbers)
    if op == "$avg":
        return sum(numbers) / len(numbers) if numbers else None
    raise NotImplementedError(op)


def _group(docs, spec):
    key_expr = spec["_id"]
    groups = {}
    for d in docs:
        key = ({k: evaluate(v, d) for k, v in key_expr.items()} if isinstance(key_expr, dict)
               else evaluate(key_expr, d))
        groups.setdefault(repr(key), (key, []))[1].append(d)
    return [{"_id": key, **{name: _accumulate(acc, members) for name, acc in spec.items() if name != "_id"}}
            for key, members in groups.values()]


def _bucket(docs, spec):
    bounds = spec["boundaries"]
    members = {}
    for d in docs:
        v = evaluate(spec["groupBy"], d)
        label = next((lo for lo, hi in zip(bounds, bounds[1:]) if v is not None and lo <= v < hi), spec["default"])
        members.setdefault(label, []).append(d)
    return [{"_id": label, **{name: _accumulate(acc, ds) for name, acc in spec["output"].items()}}
            for label, ds in sorted(members.items(), key=lambda kv: (isinstance(kv[0], str), kv[0]))]


def _unwind(docs, path):
    field = path[1:]
    return [{**d, field: item} for d in docs for item in (d.get(field) or [])]


class FakeCollection:
    def __init__(self, docs):
        self.docs = [dict(d) for d in docs]

    def count_documents(self, query):
        return sum(matches(d, query) for d in self.docs)

    def find(self, query=None, projection=None):
        found = [project(d, projection) if projection else dict(d) for d in self.docs if matches(d, query or {})]
        return Cursor(found)

    def distinct(self, field):
        out = set()
        for d in self.docs:
            v = d.get(field)
            out.update(v if isinstance(v, list) else [v])
        return [x for x in out if x is not None and x != ""]

    def aggregate(self, pipeline):
        docs = [dict(d) for d in self.docs]
        for stage in pipeline:
            (name, arg), = stage.items()
            if name == "$match":
                docs = [d for d in docs if matches(d, arg)]
            elif name == "$group":
                docs = _group(docs, arg)
            elif name == "$unwind":
                docs = _unwind(docs, arg)
            elif name == "$bucket":
                docs = _bucket(docs, arg)
            elif name == "$sort":
                docs = sort_docs(docs, arg.items())
            elif name == "$limit":
                docs = docs[:arg]
            else:
                raise NotImplementedError(name)
        return iter(docs)


class Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, spec, direction=None):
        spec = [(spec, direction)] if isinstance(spec, str) else spec
        self.docs = sort_docs(self.docs, spec)
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def __iter__(self):
        return iter(self.docs)
