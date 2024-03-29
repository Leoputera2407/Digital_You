import { NextRequest } from "next/server";


export const constructURL = (baseURL: string, path: string) => {
  // Ensure there's a single slash between baseURL and path
  return `${baseURL.replace(/\/$/, '')}/${path.startsWith('/') ? path.slice(1) : path}`;
}

export const getDomain = (request: NextRequest) => {
  // use env variable if set
  if (process.env.WED_DOMAIN) {
    return process.env.WEB_DOMAIN;
  }

  // next, try and build domain from headers
  const requestedHost = request.headers.get("X-Forwarded-Host");
  const requestedPort = request.headers.get("X-Forwarded-Port");
  const requestedProto = request.headers.get("X-Forwarded-Proto");
  if (requestedHost) {
    const url = request.nextUrl.clone();
    url.host = requestedHost;
    url.protocol = requestedProto || url.protocol;
    url.port = requestedPort || url.port;
    return url.origin;
  }

  // finally just use whatever is in the request
  return request.nextUrl.origin;
};

export const buildBackendHTTPUrl = (path: string) => {
  if (path.startsWith("/")) {
    return `${process.env.NEXT_PUBLIC_BACKEND_HTTP_URL}${path}`;
  }
  return `${process.env.NEXT_PUBLIC_BACKEND_HTTP_URL}/${path}`;
};

