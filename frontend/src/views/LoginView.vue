<script setup lang="ts">
import { ref } from "vue";
import { login, changePassword } from "../services/auth";
import { refreshCurrentUserProfile } from "@/services/session";

import { useRouter } from "vue-router";

const router = useRouter();


const username = ref("");
const password = ref("");
const rememberMe = ref(false);
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const requirePasswordChange = ref(false);
const newPassword = ref("");
const confirmPassword = ref("");

async function handleSubmit() {
	if (!requirePasswordChange.value) {
		if (!username.value || !password.value) {
			errorMessage.value = "Veuillez renseigner votre identifiant et votre mot de passe.";
			successMessage.value = "";
			return;
		}

		loading.value = true;
		errorMessage.value = "";
		successMessage.value = "";

		try {
			await login(username.value, password.value);
			await refreshCurrentUserProfile();
			successMessage.value = "Connexion reussie ! Redirection en cours...";
			router.push("/home");
		}
		catch (error: any) {
			if (error.response?.data?.detail === "PASSWORD_CHANGE_REQUIRED") {
				requirePasswordChange.value = true;
				errorMessage.value = "";
				successMessage.value = "Vous devez changer votre mot de passe pour continuer.";
			} else if (error.response?.data?.detail) {
				errorMessage.value = error.response.data.detail;
			} else {
				errorMessage.value = "Connexion impossible. Verifiez vos informations.";
			}
		} finally {
			loading.value = false;
		}
	} else {
		if (!newPassword.value || newPassword.value !== confirmPassword.value) {
			errorMessage.value = "Les mots de passe ne correspondent pas.";
			return;
		}

		loading.value = true;
		errorMessage.value = "";
		successMessage.value = "";

		try {
			await changePassword(username.value, password.value, newPassword.value);
			successMessage.value = "Mot de passe modifié avec succès ! Connexion en cours...";
			
			await login(username.value, newPassword.value);
			await refreshCurrentUserProfile();
			router.push("/home");
		} catch (error: any) {
			errorMessage.value = error.response?.data?.detail || "Erreur lors du changement de mot de passe.";
		} finally {
			loading.value = false;
		}
	}
}
</script>

<template>
	<main class="login-page">
		<div class="bg-glow bg-glow-one" aria-hidden="true"></div>
		<div class="bg-glow bg-glow-two" aria-hidden="true"></div>

		<section class="login-shell">
			<aside class="brand-panel">
				<p class="brand-top">GROUPE</p>

				<img src="/logo_coselec.jfif" alt="Logo COSELEC" class="logo-image" />

				<h1>COSELEC</h1>
				<p class="tagline">Espace de connexion ERP</p>
			</aside>

			<section class="form-panel">
				<h2>Se connecter</h2>
				<p class="subtitle">Accedez a votre espace professionnel.</p>

				<form @submit.prevent="handleSubmit" class="login-form">
					<template v-if="!requirePasswordChange">
						<label for="username">Identifiant</label>
						<input
							id="username"
							v-model="username"
							type="text"
							autocomplete="username"
							placeholder="ex: a.guizaoui"
						/>

						<label for="password">Mot de passe</label>
						<input
							id="password"
							v-model="password"
							type="password"
							autocomplete="current-password"
							placeholder="••••••••"
						/>

						<div class="form-row">
							<label class="remember">
								<input v-model="rememberMe" type="checkbox" />
								<span>Rester connecte</span>
							</label>
							<a href="#" @click.prevent>Mot de passe oublie ?</a>
						</div>
					</template>

					<template v-else>
						<label for="newPassword">Nouveau mot de passe</label>
						<input
							id="newPassword"
							v-model="newPassword"
							type="password"
							placeholder="Nouveau mot de passe"
						/>
						
						<label for="confirmPassword">Confirmer le mot de passe</label>
						<input
							id="confirmPassword"
							v-model="confirmPassword"
							type="password"
							placeholder="Confirmer"
						/>
					</template>

					<button :disabled="loading" type="submit">
						{{ loading ? (requirePasswordChange ? "Modification..." : "Connexion...") : (requirePasswordChange ? "Changer le mot de passe" : "Connexion") }}
					</button>

					<p v-if="errorMessage" class="feedback error">{{ errorMessage }}</p>
					<p v-if="successMessage" class="feedback success">{{ successMessage }}</p>
				</form>
			</section>
		</section>
	</main>
</template>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Manrope:wght@400;500;600;700&display=swap");

:global(*) {
	box-sizing: border-box;
}

.login-page {
	--red: #d10f2f;
	--red-dark: #97091f;
	--ink: #1d1d1d;
	--paper: #ffffff;

	min-height: 100vh;
	display: grid;
	place-items: center;
	padding: 24px;
	background:
		radial-gradient(circle at 8% 10%, rgba(209, 15, 47, 0.08), transparent 42%),
		radial-gradient(circle at 92% 90%, rgba(209, 15, 47, 0.09), transparent 40%),
		linear-gradient(145deg, #fff 0%, #fff 48%, #fff8f9 100%);
	position: relative;
	overflow: hidden;
	font-family: "Manrope", "Segoe UI", sans-serif;
}

.bg-glow {
	position: absolute;
	width: 360px;
	height: 360px;
	border-radius: 50%;
	background: radial-gradient(circle, rgba(209, 15, 47, 0.18), rgba(209, 15, 47, 0));
	filter: blur(12px);
	pointer-events: none;
	animation: float 8s ease-in-out infinite;
}

.bg-glow-one {
	top: -130px;
	left: -90px;
}

.bg-glow-two {
	bottom: -140px;
	right: -90px;
	animation-delay: -3s;
}

.login-shell {
	width: min(960px, 100%);
	min-height: 560px;
	display: grid;
	grid-template-columns: 1.05fr 1fr;
	border-radius: 24px;
	overflow: hidden;
	background: #fff;
	border: 1px solid rgba(209, 15, 47, 0.18);
	box-shadow: 0 24px 56px rgba(127, 7, 28, 0.15);
	animation: rise 550ms ease-out;
}

.brand-panel {
	background: linear-gradient(155deg, var(--red) 0%, var(--red-dark) 82%);
	color: #fff;
	display: grid;
	align-content: center;
	justify-items: center;
	text-align: center;
	padding: 44px 28px;
	gap: 10px;
}

.brand-top {
	letter-spacing: 0.55em;
	text-indent: 0.55em;
	font-size: 0.9rem;
	margin: 0;
	opacity: 0.9;
	font-family: "Barlow Condensed", sans-serif;
}

.logo-image {
	width: 140px;
	height: 140px;
	object-fit: contain;
	border-radius: 20px;
	margin-top: 6px;
	box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
	background: #fff;
	padding: 10px;
}

.brand-panel h1 {
	margin: 0;
	font-size: clamp(1.8rem, 3.2vw, 2.5rem);
	letter-spacing: 0.08em;
	font-family: "Barlow Condensed", sans-serif;
}

.tagline {
	margin: 0;
	opacity: 0.93;
	font-size: 0.95rem;
}

.form-panel {
	padding: 56px 46px;
	color: var(--ink);
	background: linear-gradient(to bottom, #ffffff 0%, #fffafa 100%);
}

.form-panel h2 {
	margin: 0;
	font-family: "Barlow Condensed", sans-serif;
	letter-spacing: 0.04em;
	color: var(--red);
	font-size: 2rem;
}

.subtitle {
	margin: 6px 0 24px;
	color: #555;
}

.login-form {
	display: grid;
	gap: 12px;
}

.login-form label {
	font-size: 0.92rem;
	font-weight: 600;
}

.login-form input[type="text"],
.login-form input[type="password"] {
	width: 100%;
	border: 1px solid #e7c8ce;
	border-radius: 12px;
	padding: 12px 14px;
	font-size: 0.98rem;
	outline: none;
	transition: border-color 160ms ease, box-shadow 160ms ease;
	background: #fff;
}

.login-form input[type="text"]:focus,
.login-form input[type="password"]:focus {
	border-color: var(--red);
	box-shadow: 0 0 0 3px rgba(209, 15, 47, 0.14);
}

.form-row {
	margin-top: 2px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 10px;
	font-size: 0.86rem;
}

.remember {
	display: inline-flex;
	align-items: center;
	gap: 8px;
}

.form-row a {
	color: var(--red);
	text-decoration: none;
	font-weight: 600;
}

.form-row a:hover {
	text-decoration: underline;
}

button {
	margin-top: 10px;
	border: none;
	border-radius: 12px;
	padding: 12px 16px;
	background: linear-gradient(145deg, var(--red) 0%, #b10f2b 100%);
	color: #fff;
	font-weight: 700;
	letter-spacing: 0.02em;
	cursor: pointer;
	transition: transform 140ms ease, box-shadow 140ms ease, opacity 140ms ease;
}

button:hover:enabled {
	transform: translateY(-1px);
	box-shadow: 0 10px 20px rgba(161, 11, 38, 0.25);
}

button:disabled {
	opacity: 0.7;
	cursor: not-allowed;
}

.feedback {
	margin: 3px 0 0;
	font-size: 0.88rem;
}

.feedback.error {
	color: #b20020;
}

.feedback.success {
	color: #1d7e39;
}

@keyframes rise {
	from {
		opacity: 0;
		transform: translateY(12px) scale(0.985);
	}
	to {
		opacity: 1;
		transform: translateY(0) scale(1);
	}
}

@keyframes float {
	0%,
	100% {
		transform: translateY(0);
	}
	50% {
		transform: translateY(-12px);
	}
}

@media (max-width: 900px) {
	.login-shell {
		grid-template-columns: 1fr;
		min-height: auto;
	}

	.brand-panel {
		padding: 30px 22px;
	}

	.form-panel {
		padding: 32px 22px;
	}

	.logo-image {
		width: 110px;
		height: 110px;
	}
}
</style>
