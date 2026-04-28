/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as _generated from "../_generated.js";
import type * as dataModel from "../dataModel.js";
import type * as login from "../login.js";
import type * as logout from "../logout.js";
import type * as minimal from "../minimal.js";
import type * as register from "../register.js";
import type * as root_test_login from "../root_test/login.js";
import type * as root_test_logout from "../root_test/logout.js";
import type * as root_test_register from "../root_test/register.js";
import type * as test from "../test.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  _generated: typeof _generated;
  dataModel: typeof dataModel;
  login: typeof login;
  logout: typeof logout;
  minimal: typeof minimal;
  register: typeof register;
  "root_test/login": typeof root_test_login;
  "root_test/logout": typeof root_test_logout;
  "root_test/register": typeof root_test_register;
  test: typeof test;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
