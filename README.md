# kgraft-analysis-tool

kgraft-analysis-tool is a simple tool capable of showing IPA cloning
decisions made by modified version of the GCC compiler:

https://github.com/marxin/gcc/tree/dump-ipa-clones

## Usage

```
$ gcc /home/marxin/Programming/linux/aesni-intel_glue.i -O2 -fdump-ipa-clones -c
$ ./kgraft-ipa-analysis.py aesni-intel_glue.i.000i.ipa-clones

[shows]
Function: fls64/63 (./arch/x86/include/asm/bitops.h:479:90)
  inlining to: __ilog2_u64/132 (include/linux/log2.h:40:5)
    inlining to: ablkcipher_request_alloc/1639 (include/linux/crypto.h:979:82)
      constprop: ablkcipher_request_alloc.constprop.8/3198 (include/linux/crypto.h:979:82)
    inlining to: helper_rfc4106_decrypt/3007 (arch/x86/crypto/aesni-intel_glue.c:1016:12)
    inlining to: helper_rfc4106_encrypt/3006 (arch/x86/crypto/aesni-intel_glue.c:939:12)

  Affected functions: 5
    __ilog2_u64/132 (include/linux/log2.h:40:5)
    ablkcipher_request_alloc/1639 (include/linux/crypto.h:979:82)
    ablkcipher_request_alloc.constprop.8/3198 (include/linux/crypto.h:979:82)
    helper_rfc4106_decrypt/3007 (arch/x86/crypto/aesni-intel_glue.c:1016:12)
    helper_rfc4106_encrypt/3006 (arch/x86/crypto/aesni-intel_glue.c:939:12)

```
