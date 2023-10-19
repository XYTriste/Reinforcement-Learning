# 笔记

## 1. STL概论与版本简介

STL提供六大组件，具体可以分为：

1. 容器（container）：其中包含了各种数据结构，如vector、list、deque、set、map等。STL容器是一种类模板。
2. 算法(algorithm)：各种常用算法例如sort、search、copy、erase。从实现的角度来看，STL算法是一种函数模板。
3. 迭代器(iterator)：迭代器是容器和算法之间的“胶合剂”，也称得上是一种“泛型指针”。从实现的角度来看，它是一种重载了`operator*`、`operator++`、`opeator--`、`operator->`等指针操作的类模板。所有的STL容器都附有自己的迭代器，原生指针也是一种迭代器。
4. 仿函数（functor，也称函数对象）：行为类似函数的一种类对象。从实现的角度来看，仿函数是重载了`operator()`的类或者类模板。函数指针可以看作是狭义的仿函数。
5. 适配器(adapter)：一种用来修饰容器、仿函数或迭代器接口的东西，例如STL提供的queue和stack虽然看似容器，但是实际上是容器适配器，因为其底部完全借助deque进行实现。改变仿函数接口的，称为仿函数适配器，其他称呼的方式也一样。
6. 分配器(allocator)：负责空间的分配与管理。从实现的角度来看，分配器是一个实现了动态空间分配与管理及释放的类模板。

本章其他内容非常基础，以几小点概况：

- 恰当的使用临时变量，可以节省内存空间。
- 如果是静态的、整数型（int、long等）的类"常量"，则可以也应该在定义类的内部进行初始化。
- 迭代器的迭代遵循的是左开右闭的区间，也就是`[first, last)`。其迭代范围从`first`到`last-1`。

## 2. 空间分配器

### 2.1 JJ::allocator

`jjalloc.h`:

```cpp
#progma once
/*
`#pragma once` 是一种预处理编译指令，通常放置在C++源文件的开头。它的作用是确保在编译过程中只包含一次特定的头文件，以防止重复包含。这可以提高编译效率并避免潜在的编译错误。

当你在多个源文件中包含同一个头文件时，`#pragma once` 可以确保编译器只处理该头文件一次，而不管它被多次包含。

这是一种用于头文件的常见约定，虽然在不同的编译器和操作系统中可能有其他方式来实现相同的效果，但 `#pragma once` 是一种跨平台且广泛支持的方法。
*/
#ifndef _JJALLOC_
#define _JJALLOC_

#include<new>
#include<cstddef>
#include<cstdlib>
#include<climits>
#include<iostream>

namespace JJ {

	template<class T>
	inline T* _allocate(ptrdiff_t size, T*) {	// 分配内存的函数，分配成功时返回新内存的起始地址
		std::set_new_handler(0);			// 禁用默认的异常处理函数，内存分配失败时不会抛出std::bad_alloc异常
		T* tmp = (T*)(::operator new((size_t)(size * sizeof(T))));	// 尝试分配size * sizeof(T)字节大小的内存
		if (tmp == nullptr) {
			std::cerr << "out of memory" << std::endl;
			exit(1);
		}
		return tmp;
	}

	template<class T>
	inline void _deallocate(T* buffer) {
		::operator delete(buffer);
	}

	template<class T1, class T2>
	inline void _construct(T1* p, const T2& value) {	// 在已分配的内存上构造对象
		new(p) T1(value);		// 使用定位new运算符，指定创建对象的位置
	}

	template<class T>
	inline void _destroy(T* ptr) {	// 销毁创建的对象
		ptr->~T();
	}

	
	template<class T>
	class allocator {
	public:
		typedef T value_type;
		typedef T* pointer;
		typedef const T* const_pointer;
		typedef T& reference;
		typedef const T& const_reference;
		typedef size_t size_type;
		typedef ptrdiff_t difference_type;

		allocator() = default;

		template<class U>
		allocator(const allocator<U>&) {}

		//hint used for locality
		pointer allocate(size_type n, const void* hint = 0) {
			return _allocate((difference_type)n, (pointer)0);
		}

		void deallocate(pointer p, size_type n) {
			_deallocate(p);
		}

		void construct(pointer p, const T& value) {
			_construct(p, value);
		}

		void destroy(pointer p) {
			_destroy(p);
		}

		pointer address(reference x) {
			return (pointer)&x;
		}

		const_pointer const_address(const_reference x) {
			return (const_pointer)&x;
		}

		size_type max_size() const {
			return size_type(UINT_MAX / sizeof(T));
		}
	};
}
#endif _JJALLOC_
```

`2jjalloc.cpp`:

```cpp
#include "jjalloc.h"
#include<vector>
#include<iostream>
using namespace std;

int main() {
	int ia[5] = {0,1,2,3,4};

	vector<int, JJ::allocator<int>> iv(ia, ia + 5);
	for (auto& i : iv) {
		cout << i << " ";
	}
	cout << endl;
	return 0;
}
```

这里贴出代码的原因是在初次编写这段代码的过程中遇到了一些问题，因此做笔记写出原因，后续如果没有遇到特别大的问题，则仅附上书页或文件名。

首先，在`jjalloc.h`的`allocator`类中包含如下代码（书上包含，笔记中贴出的是正确代码）：

```cpp
template<class U>
struct rebind{
	typedef allocator<U> other;
};
```

最初我没有修改这段代码时，当我在`2jjalloc.cpp`中编译代码时，代码无法通过编译并提示：“不存在从`allocator<int>到allocator<U>的转换`”，通常这样的错误都出现在没有定义相应的拷贝操作的情况下。

但是，之前学过的知识告诉我，如果我们没有编写自己的构造函数，则编译器会为我们默认生成，上面的代码也可看出我们的确没有定义任何构造函数。因此我一直找不到错误。

然而，我在未修改任何代码的情况下将这段代码放到洛谷的在线IDE中运行时，可以正常编译并输出结果。也就是说问题无非出现在编译器使用的C++版本或者某个选项导致的编译结果不同（具体什么原因，暂时不得而知）。

后续我将书上的代码删除，并修改为这段代码：

```cpp
allocator() = default;

template<class U>
allocator(const allocator<U>&) {}
```

于是可以在vs2022中正常编译运行了。

值得注意的一件事是，我们显式定义了我们的拷贝构造函数（即使没有做出任何操作），提供了从任何类型的`allocator<U>`到`allocator<T>`的转换，因此之前提示的错误不再出现了。

还有一个插曲就是，一开始我并没有写出：`allocator() = default;`，因为我期待编译器会为我生成默认的构造函数。

但是需要注意的是:<font color="red">编译器只有在我们没有定义任何的默认构造函数时才会为我们生成，也就是说如果我们自己自定义了拷贝构造函数（从形式上来看它就像一个普通的构造函数），编译器就不再为我们生成默认的构造函数了。而如果要将`allocator`应用于STL容器，则需要提供默认的无参构造函数，因此我们指定`=default`来要求编译器生成。</font>

### 2.2 SGI版本的STL空间分配器

在VC或CB系列的版本中，分配器的标准写法为：

```cpp
vector<int, std::allocator<int>> iv;
```

而在SGI中：

```cpp
vector<int, std::alloc> iv;
```

#### 2.2.1 SGI的标准空间分配器，std::allocator

代码在书中P48.

#### 2.2.2 SGI特殊的空间分配器，std::alloc

一般来说，我们通过这样的方式完成C++的内存分配与回收：

```cpp
class Foo{...};
Foo *f = new Foo;
delete f;
```

这里我们使用了`new`和`delete`关键字来完成内存管理，但是实际上它经历了这么几个阶段:

1. new操作符调用`::operator new()`函数，它是C++标准的全局内存分配函数，实际由它分配内存。
2. 内存分配完成后，new操作符继续调用Foo的构造函数，完成对象的构造。

`delete`关键字做了类似的事，只不过顺序相反，先完成对象的析构再释放内存。

为了精密分工，`STL allocator`将这两阶段的操作区分开来（正如我们在2.1节展示的代码一样）。内存分配及回收分别由`::opetator new`和`::operator delete`负责，而对象的构造和析构则由`::construct()`和`::destroy()`负责。

#### 2.2.3 construct()和destroy()

代码在书中P51。

这部分代码主要介绍了`stl_construct.h`的部分核心内容。使用定位new运算符在已分配好的内存上构建对象，在销毁对象的过程中进行了一些提升效率的操作。在销毁某个对象时，判断该对象类型的析构函数是否是"平凡的"，对于一个具有平凡析构函数的类对象而言，它不需要执行任何的内存清理操作，因此如果我们不再使用它了，下次在它所在的内存空间中直接使用定位`new`运算符来创建对象（或别的操作）覆盖它即可。

而如果一个对象类型的析构函数是“不平凡”的，那我们就只能老老实实的调用它的析构函数了，这样才能确保内存被正确的释放。

> 在 C++ 中，一个“trivial destructor”（平凡析构函数）是一个在对象销毁时不执行任何额外操作的析构函数。具体来说，平凡析构函数有以下特点：
>
> 1. 它不显式定义。
> 2. 如果类没有显式定义析构函数，编译器会生成一个默认的平凡析构函数。
> 3. 平凡析构函数不会调用任何基类或成员对象的析构函数。
> 4. 它不会释放动态分配的内存，不会关闭文件，不会执行其他清理操作。
>
> 这就意味着对于包含内置数据类型（如 `int`、`double`）或者内部对象（它们自己也有平凡析构函数）的简单类，通常不需要显式定义析构函数，因为编译器生成的默认析构函数足够。
>
> 然而，当类包含指向动态分配内存的指针、打开文件或有其他需要在对象销毁时进行清理的资源时，你可能需要显式定义析构函数来确保这些资源被正确释放，以避免内存泄漏和资源泄漏。
>
> 要注意的是，C++11 引入了 `= default` 和 `= delete` 的语法，允许你显式指定一个析构函数是否平凡，以及是否可访问。这可以提供更精确的控制。
>
> 这里额外提一点，在析构函数中使用`std::cout`也会被视为“执行了额外操作”。

#### 2.2.4 std::alloc

这部分比较复杂，我尝试进行一点一点的解释。

首先，这部分过程（即内存的分配与释放）发生在上一节的`construct()`和`destroy()`之前（内存释放当然在这过程之后）。

整个内存的配置的设计主要考虑如下几点:

- 向系统的内存堆要求得到内存
- 考虑多线程的状态
- 考虑内存不足时的措施
- 考虑过多“小块内存”造成的内存碎片问题。

其中书中主要涉及到了除多线程以外的所有点。

内存配置的基本操作就是`::operator new()`和`::operator() delete`，它们的地位就相当于`malloc()`和`free()`。

考虑小块内存带来的内存碎片的问题，SGI设计中使用了双层内存分配器。第一层内存分配器直接使用`malloc()`和`free()`，而第二层内存分配器根据不同的情况采用相应的策略：如果分配区块大小大于128字节，则认为分配了一个较大的区块，直接使用第一层的内存分配器。如果分配区块大小小于128字节，则采用复杂的内存池整理的方式。

> 在 SGI STL（史丹佛标准模板库）中，`__USE_MALLOC` 宏的定义通常用于控制 STL 中的内存分配策略。具体来说，如果 `__USE_MALLOC` 宏被定义，SGI STL 将使用 `malloc` 和 `free` 等标准 C 函数来执行内存分配和释放，而不是使用 C++ 中的 `new` 和 `delete` 运算符。这可以用于切换 STL 的内存管理方式。
>
> `__USE_MALLOC` 宏的定义可能会影响 STL 中的内存分配性能和行为。使用 `malloc` 和 `free` 可能会更快，但与 C++ 内存管理兼容性较差。如果你需要使用 STL，可以根据你的具体需求和性能要求来决定是否定义 `__USE_MALLOC` 宏。
>
> 请注意，SGI STL 是一个较早的 STL 实现，而现代的 C++ 标准库在内存管理方面进行了改进，使用 C++ 标准库通常是更好的选择，特别是在新的 C++ 项目中。

<font color="red">注意，默认情况下SGI STL并未定义`__USE_MALLOC`。</font>

也就是说，默认情况下仍然使用`new`和`delete`进行内存配置。但是无论使用哪种方式，SGI都为其包装了一个接口：

```cpp
template<class T, class Alloc>
class simple_alloc{
	public:
		static T* allocate(size_t n){
			return 0==n ? 0 : (T*) Alloc::allocate(n * sizeof(T));
		}
		static T* deallocate(void){
			return (T*) Alloc::allocate(sizeof(T));
		}
		static void deallocate(T *p, size_t n){
			if(0 != n){
				Alloc::deallocate(p, n * sizeof(T));
			}
		}
		static void deallocate(T* p){
			Alloc::deallocate(p, sizeof(T));
		}
}
```

上述类只是定义了一个简单的接口模板类，具体调用的仍然是实现该接口的实体类分配器对象。

#### 2.2.5 第一层配置器__malloc_alloc_template 剖析

代码在P56。这段代码其实很好理解，我简单解释它做了些什么。

首先它定义了默认的内存分配函数，在默认分配内存时如果分配失败，则会调用处理内存不足的函数。此外，如果需要重新分配内存，则也进行相同的操作。

用于处理内存不足的函数(`oom_malloc`)中定义了一个函数指针，该指针用于接收处理内存异常的`new-handler`函数（正如Effective C++的条款49提到的，该函数用于处理具体的内存配置问题，例如释放内存或者别的操作）。接着，在`oom_malloc`函数中会调用一个死循环，循环中会不断调用`new-handler`函数然后尝试分配内存，直到内存被成功分配返回新内存的起始地址，或者因为没有处理内存问题的`new-handler`抛出`BAD_ALLOC`异常。

#### 2.2.6. 第二层配置器__default_alloc_template 剖析

正如书中所言，如果用户在分配内存的过程中尝试多次分配了小块内存，则直接使用第一层配置器进行内存分配可能会带来内存碎片的问题。此外，多次要求系统去分配内存也会带来额外的负担。

第二层配置器针对上述问题做出了一些措施。如果要求分配的大小大于`128bytes`，那么就移交第一层配置器进行处理（说明申请的不是小块内存，不容易产生内存碎片等问题，因此第一层配置器足以处理）。反之，要求分配大小小于`128bytes`时，则移交`Memory Pool`进行处理。

`Memory Pool`究竟是如何管理内存的？我将尝试用自己的方式进行解释。

首先，这种方法又被称为次级配置：每次配置一大块内存，并且维护与之对应的自由链表。下次若有小块的内存申请，则直接从自由链表中拨出内存分配，如果释放了小块内存，则同样将其归还到自由链表中。

此外，为了方便管理，第二层配置器还会将任何小额区块的内存申请数量与8对齐（例如要求`30bytes`，实际分配`32bytes`）。

第二层配置器总共维护了16个自由链表，它们各自维护的大小分别从8、16、24、...、128，自由链表的节点结构如下：

```cpp
union obj{
	union obj* free_list_link;
	char client_data[1];
}
```

<font color="red">下述内容详细代码在P61，这里按理解进行筛选讲解。</font>

当我们实现一个第二层配置器时，首先我们需要进行上述所说的内存对齐（这与机器有关，32位机器上使用4字节对齐，64位机器上则时8字节对齐）：

```cpp
enum {__ALIGN = 8}; // 小块内存对齐的标准
enum {__MAX_BYTES = 128};	//	小块内存的上限
enum {__NFREELISTS = __MAX_BYTES / __ALIGN};	//	维护的自由链表个数
```

已知了自由链表的个数，我们就可以定义指针数组，每个元素都是一个自由链表的头节点，分别指向了不同大小的内存块：

```cpp
static obj* volatile free_list[__NFREELISTS];
```

例如，`free_list[0]`就可以表示为一个自由链表的头节点，它负责维护一个"每个节点均为8字节大小"的自由链表，而`free_list[2]`就可以表示一个"每个节点均为24字节大小"的自由链表，以此类推。

据此，我们可以使用该函数来计算每次申请内存时，实际分配的字节数：

```cpp
static size_t ROUND_UP(size_t bytes){
	return (((bytes) + __ALIGN - 1) & ~(__ALIGN - 1));
}
```

> 这个函数的功能是将给定的 `bytes` 向上舍入到最接近的较大的、满足特定对齐要求的值，并返回结果。
>
> 具体来说，函数的功能如下：
>
> 1. `(bytes) + __ALIGN - 1`：首先，将 `bytes` 与特定对齐值 `__ALIGN` 相加，并减去1。这一步的目的是将 `bytes` 向上舍入到最接近的较大的满足对齐要求的值。
> 2. `& ~(__ALIGN - 1)`：接下来，使用位掩码 `~(__ALIGN - 1)` 对结果进行按位与运算。位掩码的目的是将结果的最后 `__ALIGN` 位设置为零，从而确保对齐要求得到满足。这将确保 `bytes` 被向上对齐到 `__ALIGN` 的倍数。
> 3. 最终，函数返回向上舍入的结果，以满足特定的对齐要求。

已知了我们需要的内存大小，我们就可以据此知道去哪个自由链表中申请合适大小的内存了：

```cpp
static size_t FREELIST_INDEX(size_t bytes){
	return ((bytes + __ALIGN - 1) / __ALIGN - 1);
}
```

这将计算我们所需要的内存大小在第几个自由链表中进行申请。

特别说明的是，为什么自由链表的节点采用`union`？这是因为在一个`union`中，不论包含了多少个成员，它们同时只能存在一个有效值。且所有成员的起始地址相同。而在作为自由链表的节点时，未进行分配时我们使用`free_list_link`指向另一个节点形成链表。而当我们取出了一个节点时，我们就不再使用它的`free_list_link`了，表明这个节点已经分配给用户使用。

> 你的描述关于`Memory Pool`和第二层配置器是非常清晰的。以下是我对你描述的几点补充和建议：
>
> 1. **次级配置器的目的**：你提到了次级配置器的工作原理，但可以进一步强调它的目的是为了提高小块内存的分配和回收效率。传统的内存分配器可能在处理大量小块内存请求时效率不高，而次级配置器通过预先分配大块内存并维护自由链表来解决这个问题。
>
> 2. **对齐的重要性**：你提到了内存对齐，这是非常重要的。对齐可以确保内存访问的速度和效率，特别是在某些硬件平台上，未对齐的内存访问可能会导致性能下降或其他问题。
>
> 3. **`union`的使用**：你对`union`的描述是正确的。使用`union`确实是为了在不同的情境下复用同一块内存，既可以作为链表节点，也可以作为用户数据存储。这种设计是为了节省内存和提高效率。
>
> 4. **代码注释**：你的代码注释非常有助于理解代码的功能，特别是对于`ROUND_UP`和`FREELIST_INDEX`函数的解释。这样的注释可以帮助读者更快地理解代码的目的和工作原理。
>
> 总的来说，你的描述是非常详细和准确的，为读者提供了一个清晰的视角来理解`Memory Pool`和第二层配置器的工作原理。

#### 2.2.7 空间配置函数allocate()

这部分实际上就是刚才描述第二层分配器的具体实现，具体代码在P62。

此函数首先判断要求的内存大小，大于128字节则交给第一层配置器调用。小于128字节则计算用于分配内存的自由链表的下标。如果对应的链表中已经没有可用节点（没有合适的内存了），则调用`refill(ROUND_UP(n))`函数来重新填充对应的自由链表（refill的实现等会说）。如果节点可用，则取出该节点，并将指针指向该链表中的下一个节点（有点像头插法，但是是“头取”）。

```cpp
static void * allocate(size_t n){
	obj * volatile * my_free_list;
	obj * result;
	
	if(n > (size_t) __MAX_BYTES){
		return (malloc_alloc::allocate(n));
	}
	my_free_list = free_list + FREELIST_INDEX(n);
	result = *my_free_list;
	if(return == nullptr){
		void *r = refill(ROUND_UP(n));
		return r;
	}
	*my_free_list = result->free_list_link;
	return result;
}
```

#### 2.2.8 空间释放函数deallocate()

与`allocate()`类似，回收时它遵循着同样的原则。如果回收的内存块大于128字节，则交由第一层配置器回收，否则将其交还给对应的`free_list`。

```cpp
static void deallocate(void *p, size_t n){
	obj *q = (obj *) p;
	obj * volatile * my_free_list;
	if(n > (size_t) __MAX_BYTES){
		malloc_alloc::deallocate(p, n);
		return;
	}
	my_free_list = free_list + FREELIST_INDEX(n);
	q->free_list_link = *my_free_list;
	*my_free_list = q;	//这下真的是头插法了。
}
```

#### 2.2.9 重新填充free lists

在我们上面所提到的`allocate()`函数中，当自由链表中已经没有可用的节点时，我们会尝试重新填充该自由链表并分配内存给用户，这部分依靠我们的`refill(size_t n)`实现。

`refill`函数将从内存池中，经由`chunk_alloc`函数来取得20个新节点。如果内存池中没有 20 * 每个节点大小 的内存，则获得的节点数可能小于20：

```cpp
//注意，上述allocate中调用该函数时嵌套调用了ROUND_UP函数，因此n是一个8字节对齐的数字。
void * __default_alloc_template<threads, inst>::refill(size_t n){
	int nobjs = 20;		// 默认取得20个节点
	//尝试取得nobjs个大小为n的节点
	char * chunk = chunk_alloc(n, nobjs);	// 这里的第二个参数传递的是引用，由它返回实际取得的节点数量。
	obj * volatile * my_free_list;
	obj * result;
	obj * current_obj, *next_obj;
	int i;
	
	//如果chunk_alloc只得到了一个内存块，那么该内存块交给用户使用，free_list不会得到新的节点。
	if(nobjs == 1){
		return chunk;
	}
	//否则调整free_list来容纳新的节点
	my_free_list = free_list + FREELIST_INDEX(n);
	
	result = (obj *)chunk;	// 得到了nobjs(nobjs > 1)个节点，将第1个节点返回给用户。
	*my_free_list = next_obj = (obj *)(chunk + n);	//	注意chunk在声明时声明为char *类型，因此偏移n实际上就是偏移n个字节，即正好一个节点的大小。偏移后的地址就是free_list新得到的第一个节点的起始地址。
	for(i = 1;; i++){	// 循环将新的节点们链接起来，因为第一个节点要返回给用户，因此i从1开始。
		current_obj = next_obj;
		next_obj = (obj *)((char *)next_obj + n);	// 与上面的chunk同理
		if(nobjs - 1 == i){
			current_obj->free_list_link = nullptr;
			break;
		}else{
			current_obj->free_list_link = next_obj;
		}
	}
	return result;
}
```

#### 2.2.10 内存池

内存池的主要功能是经由`chunk_alloc`分配内存给`free_list`使用。这部分代码较长，在书上P66~P68。

下面简单叙述`chunk_alloc`的功能：

首先，我们检查内存池的剩余空间，如果完全满足需要（n * nobjs个字节），那么直接分配。

如果不能满足(n * nobjs)，但是可以分配至少1个n字节大小的内存，那么就分配尽可能多（1或1以上）个n字节大小的内存。

如果连一个n字节大小的内存都不够，则将内存池中剩下的内存尽可能分配给自由链表（比如还剩31字节，则分配给24字节的自由链表，剩下7字节则浪费了）。然后向系统堆申请新的内存空间用于内存池。

如果堆中不够内存，`malloc`失败，