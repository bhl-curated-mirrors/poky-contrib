/**
 * Copyright (c) 2016 Intel Corporation
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 *
 * AUTHORS
 * 	Aníbal Limón <anibal.limon@intel.com>
 */

#include <ctype.h>
#include <limits.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

#ifdef MEMCHECK
#ifdef RELEASE
#error "You can't use MEMCHECK when RELEASE is active."
#endif

#include <mcheck.h>
#endif

#include "utils.h"
#include "flags.h"

#define DEFAULT_DIRECTORY "/usr/lib"
#define DEFAULT_TIMEOUT 300

static inline void
print_usage(FILE *stream, char *progname)
{
	fprintf(stream, "Usage: %s [-d directory] [-e exclude] [-l list] [-t timeout]"
			" [-x xml-filename] [-h] [ptest1 ptest2 ...]\n", progname);
}

int
main(int argc, char *argv[])
{
	int opt;
	int ptest_num = 0;
	int i;
	int rc;
	int ptest_exclude_num = 0;
	char *c, *tok;

#ifdef MEMCHECK
	mtrace();
#endif

	struct ptest_list *head, *run;
	struct ptest_options opts;

	opts.directory = strdup(DEFAULT_DIRECTORY);
	opts.exclude = NULL;
	opts.list = 0;
	opts.timeout = DEFAULT_TIMEOUT;
	opts.ptests = NULL;
	opts.xml_filename = NULL;
	opts.flags = 0;

	while ((opt = getopt(argc, argv, "d:e:lt:x:Lh")) != -1) {
		switch (opt) {
			case 'd':
				free(opts.directory);
				opts.directory = realpath(optarg, NULL);
				CHECK_ALLOCATION(opts.directory, 1, 1);
			break;
			case 'e':
				c = optarg;
				ptest_exclude_num = 1;

				while (*c) {
					if (isspace(*c))
						ptest_exclude_num++;
					c++;
				}


				opts.exclude = malloc(ptest_exclude_num * sizeof(char));
				CHECK_ALLOCATION(opts.exclude, 1, 1);

				i = 0;
				tok = strtok_r(optarg, " ", &c);
				opts.exclude[i] = strdup(tok);
				CHECK_ALLOCATION(opts.exclude[i], 1, 1);
				i++;
				while ((tok = strtok_r(NULL, " ", &c)) != NULL) {
					opts.exclude[i] = strdup(tok);
					CHECK_ALLOCATION(opts.exclude[i], 1, 1);
					i++;
				}
			break;
			case 'l':
				opts.list = 1;
			break;
			case 't':
				opts.timeout = atoi(optarg);
			break;
			case 'h':
				print_usage(stdout, argv[0]);
				exit(0);
			break;
			case 'x':
				free(opts.xml_filename);
				opts.xml_filename = strdup(optarg);
				CHECK_ALLOCATION(opts.xml_filename, 1, 1);
			break;
			case 'L':
				// set LAVA signal mode
				opts.flags |= LAVA_SIGNAL_ENABLE;
				fprintf(stdout, "LAVA_SIGNAL_ENABLE == %d\n", opts.flags);
			break;
			default:
				print_usage(stdout, argv[0]);
				exit(1);
			break;
		}
	}

	ptest_num = argc - optind;
	if (ptest_num > 0) {
		size_t size = ptest_num * sizeof(char *);
		opts.ptests = calloc(1, size);
		CHECK_ALLOCATION(opts.ptests, size, 1);

		for (i = 0; i < ptest_num; i++) {
			opts.ptests[i] = strdup(argv[argc - ptest_num + i]);
			CHECK_ALLOCATION(opts.ptests[i], 1, 1);
		}
	}

	head = get_available_ptests(opts.directory);
	if (head == NULL || ptest_list_length(head) == 0) {
		fprintf(stderr, PRINT_PTESTS_NOT_FOUND);
		return 1;
	}

	if (opts.list) {
		print_ptests(head, stdout);
		return 0;
	}

	run = head;
	if (ptest_num > 0) {
		for (i = 0; i < ptest_num; i++) {
			if (ptest_list_search(head, opts.ptests[i]) == NULL) {
				fprintf(stderr, "%s ptest isn't available.\n",
					opts.ptests[i]);
				return 1;
			}
		}

		run = filter_ptests(head, opts.ptests, ptest_num);
		CHECK_ALLOCATION(run, ptest_num, 1);
		ptest_list_free_all(head);
	}

	for (i = 0; i < ptest_exclude_num; i++)
		ptest_list_remove(run, opts.exclude[i], 1);

	rc = run_ptests(run, opts, argv[0], stdout, stderr);

	ptest_list_free_all(run);

	return rc;
}
