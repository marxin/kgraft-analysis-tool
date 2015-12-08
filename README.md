# kgraft-analysis-tool

kgraft-analysis-tool is a simple tool capable of showing IPA cloning
decisions made by modified version of the GCC compiler:
https://github.com/marxin/gcc/tree/dump-ipa-clones

Having a modifed function __foo__, the tool displays all functions that
can be affected by a change applied to the function __foo__.
The most common case is propagation via inlining, however there are
another IPA passes (IPA split, IPA constant propagation, etc.)
that can be eventually generate clones that are inlined to a function.

## Usages

```
$ gcc /home/marxin/Programming/linux/aesni-intel_glue.i -O2 -fdump-ipa-clones -c
$ ./kgraft-ipa-analysis.py aesni-intel_glue.i.000i.ipa-clones

[..skipped..]
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
[..skipped..]
```

The tool can be easily used to display just a single function:

```
$ ./kgraft-ipa-analysis.py --symbol=scatterwalk_unmap aesni-intel_glue.i.000i.ipa-clones
Function: scatterwalk_unmap/2930 (include/crypto/scatterwalk.h:81:60)
  isra: scatterwalk_unmap.isra.2/3142 (include/crypto/scatterwalk.h:81:60)
    inlining to: helper_rfc4106_decrypt/3007 (arch/x86/crypto/aesni-intel_glue.c:1016:12)
    inlining to: helper_rfc4106_decrypt/3007 (arch/x86/crypto/aesni-intel_glue.c:1016:12)
    inlining to: helper_rfc4106_encrypt/3006 (arch/x86/crypto/aesni-intel_glue.c:939:12)

  Affected functions: 3
    scatterwalk_unmap.isra.2/3142 (include/crypto/scatterwalk.h:81:60)
    helper_rfc4106_decrypt/3007 (arch/x86/crypto/aesni-intel_glue.c:1016:12)
    helper_rfc4106_encrypt/3006 (arch/x86/crypto/aesni-intel_glue.c:939:12)
```
