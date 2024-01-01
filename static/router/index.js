import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import AdminLogin from "../components/admin-login.vue";
import UserLogin from "../components/user-login.vue";
import UserSignup from "../components/user-signup.vue";
import ManagerDash from "../components/manager-dash.vue";
import CreateCategory from "../components/create-category.vue";
import CreateProduct from "../components/create-product.vue";
import EditCategory from "../components/edit-category.vue";
import EditProduct from "../components/edit-product.vue";
import UserDash from "../components/user-dash.vue";
import UserProfile from "../components/user-profile.vue";
import BuyProduct from "../components/buy-product.vue";
import ManagerLogin from "../components/manager-login.vue";
import ManagerSignup from "../components/manager-signup.vue";
import AdminDash from "../components/admin-dash.vue";
import UserCart from "../components/user-cart.vue";
import EditCart from "../components/edit-cart.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/admin-login",
    name: "admin-login",
    component: AdminLogin,
  },
  {
    path: "/user-login",
    name: "user-login",
    component: UserLogin,
  },
  {
    path: "/user-signup",
    name: "user-signup",
    component: UserSignup,
  },
  {
    path: "/manager-dash",
    name: "manager-dash",
    component: ManagerDash,
  },
  {
    path: "/create-category",
    name: "create-category",
    component: CreateCategory,
  },
  {
    path: "/create-product",
    name: "create-product",
    component: CreateProduct,
  },
  {
    path: "/edit-category",
    name: "edit-category",
    component: EditCategory,
  },
  {
    path: "/edit-product",
    name: "edit-product",
    component: EditProduct,
  },
  {
    path: "/user-dash",
    name: "user-dash",
    component: UserDash,
  },
  {
    path: "/user-dash/user-profile",
    name: "user-profile",
    component: UserProfile,
  },
  {
    path: "/user-dash/buy-product",
    name: "buy-product",
    component: BuyProduct,
  },
  {
    path: "/manager-login",
    name: "manager-login",
    component: ManagerLogin,
  },
  {
    path: "/manager-signup",
    name: "manager-signup",
    component: ManagerSignup,
  },
  {
    path: "/admin-dash",
    name: "admin-dash",
    component: AdminDash,
  },
  {
    path: "/user-dash/buy-product/user-cart",
    name: "user-cart",
    component: UserCart,
  },
  {
    path: "/user-dash/buy-product/user-cart/edit-cart",
    name: "edit-cart",
    component: EditCart,
  },
];

const router = new VueRouter({
  routes,
});

export default router;
