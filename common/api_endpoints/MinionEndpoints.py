

class MinionEndpoints:
    class GET:
        HEALTH = "/health"
        STATUS = "/status/{hash_value}/{start_range}/{end_range}"

    class POST:
        CRACK = "/crack"