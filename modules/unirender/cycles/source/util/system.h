/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __UTIL_SYSTEM_H__
#define __UTIL_SYSTEM_H__

#include "util/string.h"
#include "util/vector.h"

CCL_NAMESPACE_BEGIN

/* Get width in characters of the current console output. */
int system_console_width();

string system_cpu_brand_string();
int system_cpu_bits();
bool system_cpu_support_sse2();
bool system_cpu_support_sse3();
bool system_cpu_support_sse41();
bool system_cpu_support_avx();
bool system_cpu_support_avx2();

size_t system_physical_ram();

/* Start a new process of the current application with the given arguments. */
bool system_call_self(const vector<string> &args);

/* Get identifier of the currently running process. */
uint64_t system_self_process_id();

CCL_NAMESPACE_END

#endif /* __UTIL_SYSTEM_H__ */
