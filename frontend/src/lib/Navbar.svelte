<script>
    import { Link } from "svelte-routing";
    let isNavOpen = false;

    function toggleNav() {
        isNavOpen = !isNavOpen;
    }
</script>

<nav class="navbar navbar-expand-lg navbar-light app-navbar">
    <div class="container-fluid">
        <Link class="navbar-brand" to="/">
            <img src="/shrimp-health.svg" alt="Logo deteksi penyakit udang vannamei" width="30" height="24" class="d-inline-block align-text-top">
            Deteksi Penyakit Udang Vannamei
        </Link>
        <button class="navbar-toggler" type="button" on:click={toggleNav}>
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" class:show={isNavOpen} id="navbarNav">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                    <Link class="nav-link" to="/" on:click={toggleNav}>Dashboard</Link>
                </li>
                <li class="nav-item">
                    <Link class="nav-link" to="/live" on:click={toggleNav}>Deteksi Real-time</Link>
                </li>
                <li class="nav-item">
                    <Link class="nav-link" to="/image" on:click={toggleNav}>Deteksi Foto</Link>
                </li>
                <li class="nav-item">
                    <Link class="nav-link" to="/batch" on:click={toggleNav}>Analisis Video</Link>
                </li>
            </ul>
        </div>
    </div>
</nav>
