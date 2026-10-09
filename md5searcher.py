from hashlib import md5
import multiprocessing


class MD5Searcher:

    def __init__(self):
        pass

    def loop_for_hash(self, start, end, target, found_flag, result_number):
        for i in range(start, end):
            # Exit early if another process already found the hash
            if found_flag.value:
                break
            if md5(str(i).encode("utf-8")).hexdigest() == target:
                found_flag.value = True
                result_number.value = i
                break

    def find_hash(self, target_hash, number_of_processors, start, end):
        # Use shared multiprocessing variables
        found_flag = multiprocessing.Value('b', False)  # 'b' for boolean
        result_number = multiprocessing.Value('i', -1)  # 'i' for integer

        processors_list = []
        sep = (end - start) // number_of_processors
        s = start

        for i in range(number_of_processors):
            # Ensure the last process covers any remaining remainder
            e = s + sep if i < number_of_processors - 1 else end
            if s >= e:
                break

            p = multiprocessing.Process(
                target=self.loop_for_hash,
                args=(s, e, target_hash, found_flag, result_number)
            )
            processors_list.append(p)
            p.start()
            s = e

        # Wait for all processes to complete
        for p in processors_list:
            p.join()

        if found_flag.value:
            return result_number.value
        else:
            return -1



if __name__ == '__main__':
    h = md5("100".encode()).hexdigest()
    m = MD5Searcher()
    print(m.find_hash(h, 8, 0, 1000))